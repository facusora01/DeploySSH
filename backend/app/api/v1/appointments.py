import uuid
import time
import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.api.deps import get_current_cliente, get_current_user, get_db, get_appointment_service
from app.models.appointment import Appointment, AppointmentStatus, DepositStatus
from app.models.form_field import FormField, FormFieldResponse
from app.models.service import Service
from app.models.client import Client
from app.models.user import User
from app.schemas.appointment import (
    AppointmentAttendanceUpdate,
    AppointmentCancel,
    AppointmentCreate,
    AppointmentResponse,
)
from app.services.appointment_service import AppointmentService
from app.services.email import send_appointment_confirmation
from app.services.whatsapp import send_appointment_confirmation as send_whatsapp_confirmation

router = APIRouter(tags=["appointments"])


def _schedule_confirmations(background_tasks: BackgroundTasks, user: User, service: Service, appointment: Appointment) -> None:
    """Agenda el envío de email y WhatsApp de confirmación del turno en background."""
    import asyncio

    start_time = appointment.start_time
    profesional_name = appointment.profesional_name

    if user.email:
        def send_email_sync():
            print(f"[EMAIL] Iniciando envio a {user.email}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    send_appointment_confirmation(
                        recipient_email=user.email,
                        client_name=user.full_name,
                        service_name=service.name,
                        start_time=start_time.strftime("%d/%m/%Y %H:%M"),
                        profesional_name=profesional_name,
                    )
                )
                print(f"[EMAIL] Resultado: {result}")
            except Exception as e:
                print(f"[EMAIL] Error: {e}")
            finally:
                loop.close()

        background_tasks.add_task(send_email_sync)

    if user.phone:
        def send_whatsapp_sync():
            print(f"[WHATSAPP] Iniciando envio a {user.phone}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    send_whatsapp_confirmation(
                        phone_number=user.phone,
                        client_name=user.full_name,
                        service_name=service.name,
                        start_time=start_time,
                        profesional_name=profesional_name,
                    )
                )
                print(f"[WHATSAPP] Resultado: {result}")
            except Exception as e:
                print(f"[WHATSAPP] Error: {e}")
            finally:
                loop.close()

        background_tasks.add_task(send_whatsapp_sync)


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_cliente),
    db: Session = Depends(get_db)
):
    # 1. Fetch service
    service = db.query(Service).filter(Service.id == payload.service_id).first()
    if not service or not service.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )
    
    profesional = service.profesional
    if not profesional or profesional.agenda_paused:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La agenda de este profesional está pausada"
        )
    
    # 2. Get client profile
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        client = Client(user_id=current_user.id)
        db.add(client)
        db.flush()
        
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
    occ_count = db.query(Appointment).filter(
        Appointment.service_id == service.id,
        Appointment.start_time == start_time,
        Appointment.status != AppointmentStatus.CANCELLED
    ).count()

    if occ_count >= service.max_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El horario seleccionado ya está completo"
        )

    # 6. Validate form field responses
    profesional_fields = (
        db.query(FormField)
        .filter(FormField.profesional_id == profesional.id)
        .all()
    )

    submitted_ids = {r.field_id for r in payload.form_responses}
    for field in profesional_fields:
        if field.is_required and field.id not in submitted_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El campo '{field.field_name}' es obligatorio",
            )

    # Validate that submitted field_ids actually belong to this profesional
    valid_field_ids = {f.id for f in profesional_fields}
    for response in payload.form_responses:
        if response.field_id not in valid_field_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Campo de formulario no válido para este profesional",
            )

    # 7. Determine appointment status based on deposit
    deposit_status = DepositStatus.NONE
    appointment_status = AppointmentStatus.CONFIRMED

    if service.deposit_active:
        deposit_status = DepositStatus.PENDING
        appointment_status = AppointmentStatus.PENDING
        
    # 8. Create appointment
    appointment = Appointment(
        service_id=service.id,
        client_id=client.id,
        start_time=start_time,
        end_time=end_time,
        status=appointment_status,
        deposit_status=deposit_status,
        notes=payload.notes
    )

    db.add(appointment)
    db.flush()

    # 9. Save form field responses
    for response in payload.form_responses:
        db.add(FormFieldResponse(
            appointment_id=appointment.id,
            field_id=response.field_id,
            answer=response.answer,
        ))

    db.commit()
    db.refresh(appointment)

    # 9b. Notificar al profesional que se reservó un turno
    from app.services.notification_service import notify_appointment_booked
    try:
        notify_appointment_booked(db, appointment, commit=True)
    except Exception as e:
        logger.warning(f"Error creando notificación de turno reservado: {e}")

    # 10. Confirmación (email + WhatsApp) SOLO si el turno quedó CONFIRMED.
    # Con seña el turno nace PENDING: la confirmación se envía recién al pagar la
    # seña (pay_deposit) o al saltear una seña opcional (confirm_without_deposit).
    if appointment.status == AppointmentStatus.CONFIRMED:
        _schedule_confirmations(background_tasks, current_user, service, appointment)

    return appointment

@router.post("/debug/send-reminders")
def debug_send_reminders():
    """Endpoint de debug para ejecutar manualmente el envio de recordatorios"""
    from app.services.scheduler import check_and_send_reminders
    try:
        check_and_send_reminders()
        return {"status": "ok", "message": "Reminders check triggered"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/debug/send-all-reminders")
def debug_send_all_reminders(db: Session = Depends(get_db)):
    """Endpoint de debug para enviar recordatorios a TODAS las citas pendientes (sin restriccion de ventana)"""
    from app.services.whatsapp import send_appointment_reminder
    import asyncio

    try:
        appointments = db.query(Appointment).filter(
            Appointment.status == AppointmentStatus.CONFIRMED,
        ).all()

        count = 0
        for appointment in appointments:
            client = appointment.client
            if not client or not client.user or not client.user.phone:
                continue

            service = appointment.service
            if not service:
                continue

            print(f"[DEBUG] Sending WhatsApp to {client.user.phone} for {service.name}")
            asyncio.run(
                send_appointment_reminder(
                    phone_number=client.user.phone,
                    client_name=client.user.full_name,
                    service_name=service.name,
                    start_time=appointment.start_time,
                )
            )
            count += 1

        return {"status": "ok", "message": f"Sent reminders to {count} appointments"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("", response_model=list[AppointmentResponse])
def list_appointments(
    current_user: User = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    return service.list_appointments(current_user)

@router.put("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentCancel,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    return service.cancel_appointment(
        appointment_id, current_user, payload.cancellation_reason, background_tasks
    )

@router.patch("/{appointment_id}/attendance", response_model=AppointmentResponse)
def mark_attendance(
    appointment_id: uuid.UUID,
    payload: AppointmentAttendanceUpdate,
    current_user: User = Depends(get_current_user),
    service: AppointmentService = Depends(get_appointment_service),
):
    return service.mark_attendance(
        appointment_id, AppointmentStatus(payload.status), current_user
    )

@router.patch("/{appointment_id}/pay-deposit", response_model=AppointmentResponse)
def pay_deposit(
    appointment_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_cliente),
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno no encontrado"
        )

    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client or appointment.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este turno"
        )

    if appointment.deposit_status != DepositStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este turno no tiene una seña pendiente"
        )

    # Simulate payment processing
    time.sleep(1.5)

    appointment.deposit_status = DepositStatus.PAID
    appointment.status = AppointmentStatus.CONFIRMED

    db.commit()
    db.refresh(appointment)

    # Seña pagada → turno confirmado → recién acá enviamos la confirmación.
    _schedule_confirmations(background_tasks, current_user, appointment.service, appointment)

    return appointment

@router.patch("/{appointment_id}/confirm-without-deposit", response_model=AppointmentResponse)
def confirm_without_deposit(
    appointment_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_cliente),
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno no encontrado"
        )

    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client or appointment.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este turno"
        )

    if appointment.deposit_status != DepositStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este turno no tiene una seña pendiente"
        )

    if appointment.service.deposit_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La seña es obligatoria para este servicio"
        )

    # Simulate processing delay
    time.sleep(1.5)

    # Seña opcional salteada: la reserva igual vale → confirmamos sin seña.
    appointment.status = AppointmentStatus.CONFIRMED
    appointment.deposit_status = DepositStatus.NONE

    db.commit()
    db.refresh(appointment)

    # Turno confirmado (sin seña) → enviamos la confirmación.
    _schedule_confirmations(background_tasks, current_user, appointment.service, appointment)

    return appointment
