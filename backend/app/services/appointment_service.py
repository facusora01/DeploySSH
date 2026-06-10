import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

logger = logging.getLogger(__name__)

from app.core.interfaces.unit_of_work import IUnitOfWork
from app.exceptions.domain_exceptions import (
    AgendaPausedError,
    AppointmentAlreadyCancelledError,
    AppointmentForbiddenError,
    AppointmentNotFinishedError,
    AppointmentNotFoundError,
    ServiceNotFoundError,
    SlotUnavailableError,
)
from app.models.appointment import Appointment, AppointmentStatus, DepositStatus
from app.models.refund import Refund, RefundStatus
from app.models.client import Client
from app.models.local import Local
from app.models.user import User
from app.schemas.appointment import AppointmentCreate
from app.utils.email import send_appointment_cancellation_email, send_refund_pending_email


class AppointmentService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def create_appointment(
        self, payload: AppointmentCreate, current_user: User
    ) -> Appointment:
        with self.uow:
            # 1. Fetch service
            service = self.uow.service_repo.get_by_id(payload.service_id)
            if not service or not service.is_active:
                raise ServiceNotFoundError(str(payload.service_id))

            profesional = service.profesional
            if not profesional or profesional.agenda_paused:
                raise AgendaPausedError()

            # 2. Get client profile
            client = self.uow.client_repo.get_by_user_id(current_user.id)
            if not client:
                client = Client(user_id=current_user.id)
                self.uow.session.add(client)
                self.uow.session.flush()

            # 3. Update client/user details if they were passed
            if payload.full_name is not None:
                current_user.full_name = payload.full_name
            if payload.phone is not None:
                current_user.phone = payload.phone
            if payload.dni is not None:
                client.dni = payload.dni
            if payload.date_of_birth is not None:
                client.date_of_birth = payload.date_of_birth
            if payload.address is not None:
                client.address = payload.address
            if payload.city is not None:
                client.city = payload.city

            # 4. Calculate appointment duration and verify bounds
            start_time = payload.start_time
            end_time = start_time + timedelta(minutes=service.duration_minutes)

            # 5. Check occupancy at start_time
            occ_count = self.uow.appointment_repo.count_occupancy(
                service.id, start_time
            )

            if occ_count >= service.max_slots:
                raise SlotUnavailableError()

            # 6. Create appointment
            appointment = self.uow.appointment_repo.create(
                service_id=service.id,
                client_id=client.id,
                start_time=start_time,
                end_time=end_time,
                status=AppointmentStatus.CONFIRMED,
                notes=payload.notes,
            )

            self.uow.commit()
            return appointment

    def list_appointments(self, current_user: User) -> List[Appointment]:
        with self.uow:
            if current_user.role == "profesional":
                profesional = current_user.profesional
                if not profesional:
                    return []
                service_ids = [s.id for s in profesional.services]
                if not service_ids:
                    return []
                return self.uow.appointment_repo.list_by_service_ids(service_ids)
            elif current_user.role == "local":
                local = self.uow.session.query(Local).filter(Local.user_id == current_user.id).first()
                if not local:
                    return []
                service_ids = [s.id for prof in local.profesionales for s in prof.services]
                if not service_ids:
                    return []
                return self.uow.appointment_repo.list_by_service_ids(service_ids)
            else:
                client = self.uow.client_repo.get_by_user_id(current_user.id)
                if not client:
                    return []
                return self.uow.appointment_repo.list_by_client(client.id)

    def cancel_appointment(
        self,
        appointment_id: uuid.UUID,
        current_user: User,
        cancellation_reason: str = None,
        background_tasks=None,
    ) -> Appointment:
        with self.uow:
            appointment = self.uow.appointment_repo.get_by_id(appointment_id)
            if not appointment:
                raise AppointmentNotFoundError(str(appointment_id))

            if appointment.status == AppointmentStatus.CANCELLED:
                raise AppointmentAlreadyCancelledError()

            is_authorized = False
            cancelled_by_client = current_user.role in ("client", "cliente")
            if cancelled_by_client:
                if appointment.client.user_id == current_user.id:
                    is_authorized = True
            elif current_user.role == "profesional":
                if appointment.service.profesional.user_id == current_user.id:
                    is_authorized = True
                    if not cancellation_reason or len(cancellation_reason) < 5:
                        raise AppointmentForbiddenError("Cancellation reason is required and must be at least 5 characters long")
            elif current_user.role == "local":
                local = self.uow.session.query(Local).filter(Local.user_id == current_user.id).first()
                if local and appointment.service.profesional.local_id == local.id:
                    is_authorized = True
                    if not cancellation_reason or len(cancellation_reason) < 5:
                        raise AppointmentForbiddenError("Cancellation reason is required and must be at least 5 characters long")

            if not is_authorized:
                raise AppointmentForbiddenError()

            if appointment.deposit_status == "PAID":
                self._trigger_mock_refund(appointment)

            appointment.status = AppointmentStatus.CANCELLED
            appointment.cancellation_reason = cancellation_reason

            refund_needed = (
                appointment.deposit_status == DepositStatus.PAID
                and not cancelled_by_client
            )
            if refund_needed:
                refund = Refund(
                    appointment_id=appointment.id,
                    amount=appointment.service.deposit_amount,
                    status=RefundStatus.PENDING,
                )
                self.uow.session.add(refund)

            from app.services.notification_service import (
                notify_appointment_cancelled_by_client,
                notify_appointment_cancelled_by_local,
                notify_appointment_cancelled_by_profesional,
                notify_refund_pending,
            )
            cancelled_by_local = current_user.role == "local"
            if cancelled_by_client:
                notify_appointment_cancelled_by_client(self.uow.session, appointment)
            elif cancelled_by_local:
                notify_appointment_cancelled_by_profesional(self.uow.session, appointment)
                notify_appointment_cancelled_by_local(self.uow.session, appointment)
            else:
                notify_appointment_cancelled_by_profesional(self.uow.session, appointment)

            if refund_needed:
                notify_refund_pending(self.uow.session, appointment)

            self.uow.commit()

            client_user = appointment.client.user
            send_appointment_cancellation_email(
                to_email=client_user.email,
                full_name=client_user.full_name,
                service_name=appointment.service.name,
                start_time=appointment.start_time,
                profesional_name=appointment.service.profesional.user.full_name,
            )

            if refund_needed:
                profesional_user = appointment.service.profesional.user
                deposit_amount = float(appointment.service.deposit_amount or 0)
                send_refund_pending_email(
                    to_email=profesional_user.email,
                    full_name=profesional_user.full_name,
                    client_name=client_user.full_name,
                    service_name=appointment.service.name,
                    start_time=appointment.start_time,
                    deposit_amount=deposit_amount,
                )

                if background_tasks and profesional_user.phone:
                    from app.services.whatsapp import send_refund_pending_whatsapp

                    def _send_refund_whatsapp():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(
                                send_refund_pending_whatsapp(
                                    phone_number=profesional_user.phone,
                                    profesional_name=profesional_user.full_name,
                                    client_name=client_user.full_name,
                                    service_name=appointment.service.name,
                                    start_time=appointment.start_time,
                                    deposit_amount=deposit_amount,
                                )
                            )
                        except Exception as e:
                            logger.warning(f"Error sending refund WhatsApp: {e}")
                        finally:
                            loop.close()

                    background_tasks.add_task(_send_refund_whatsapp)

            return appointment

    def cancel_by_admin(
        self,
        appointment: Appointment,
        reason: str,
        background_tasks=None,
    ) -> None:
        """Cancel an appointment on behalf of the local admin. No auth check — caller is responsible."""
        if appointment.status == AppointmentStatus.CANCELLED:
            return

        if appointment.deposit_status == DepositStatus.PAID:
            self._trigger_mock_refund(appointment)

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancellation_reason = reason

        refund_needed = appointment.deposit_status == DepositStatus.PAID
        if refund_needed:
            refund = Refund(
                appointment_id=appointment.id,
                amount=appointment.service.deposit_amount,
                status=RefundStatus.PENDING,
            )
            self.uow.session.add(refund)

        from app.services.notification_service import (
            notify_appointment_cancelled_by_profesional,
            notify_refund_pending,
        )
        notify_appointment_cancelled_by_profesional(self.uow.session, appointment)
        if refund_needed:
            notify_refund_pending(self.uow.session, appointment)

        client_user = appointment.client.user
        send_appointment_cancellation_email(
            to_email=client_user.email,
            full_name=client_user.full_name,
            service_name=appointment.service.name,
            start_time=appointment.start_time,
            profesional_name=appointment.service.profesional.user.full_name,
        )

        if refund_needed:
            profesional_user = appointment.service.profesional.user
            deposit_amount = float(appointment.service.deposit_amount or 0)
            send_refund_pending_email(
                to_email=profesional_user.email,
                full_name=profesional_user.full_name,
                client_name=client_user.full_name,
                service_name=appointment.service.name,
                start_time=appointment.start_time,
                deposit_amount=deposit_amount,
            )

            if background_tasks and profesional_user.phone:
                from app.services.whatsapp import send_refund_pending_whatsapp

                def _send_refund_whatsapp():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(
                            send_refund_pending_whatsapp(
                                phone_number=profesional_user.phone,
                                profesional_name=profesional_user.full_name,
                                client_name=client_user.full_name,
                                service_name=appointment.service.name,
                                start_time=appointment.start_time,
                                deposit_amount=deposit_amount,
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Error sending refund WhatsApp: {e}")
                    finally:
                        loop.close()

                background_tasks.add_task(_send_refund_whatsapp)

    def _trigger_mock_refund(self, appointment: Appointment):
        """Simulates a refund for US-16"""
        amount = appointment.service.deposit_amount
        print(f"[MOCK REFUND] Success: Refunded {amount} for Appointment {appointment.id} (Client: {appointment.client.user.full_name})")

    def mark_attendance(
        self,
        appointment_id: uuid.UUID,
        new_status: AppointmentStatus,
        current_user: User,
    ) -> Appointment:
        with self.uow:
            appointment = self.uow.appointment_repo.get_by_id(appointment_id)
            if not appointment:
                raise AppointmentNotFoundError(str(appointment_id))

            # Solo el profesional dueño del servicio puede marcar asistencia
            is_owner = (
                current_user.role == "profesional"
                and appointment.service.profesional.user_id == current_user.id
            )
            if not is_owner:
                raise AppointmentForbiddenError()

            if new_status not in (
                AppointmentStatus.ATTENDED,
                AppointmentStatus.NO_SHOW,
            ):
                raise AppointmentForbiddenError()

            if appointment.status == AppointmentStatus.CANCELLED:
                raise AppointmentForbiddenError()

            # Se puede marcar asistencia para turnos de hoy o de días pasados,
            # pero no para turnos de días futuros.
            if appointment.start_time.date() > datetime.now(timezone.utc).date():
                raise AppointmentNotFinishedError()

            appointment.status = new_status
            self.uow.commit()
            return appointment
