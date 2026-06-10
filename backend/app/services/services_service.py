import uuid

from app.core.interfaces.unit_of_work import IUnitOfWork
from app.models.service import Service
from app.exceptions.domain_exceptions import (
    ServiceForbiddenError,
    ServiceNotFoundError,
    ServiceHasFutureAppointmentsError,
)


class ServiceService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def create_service(
        self,
        profesional_id: int,
        name: str,
        duration_minutes: int,
        price: float | None = None,
        description: str | None = None,
        max_slots: int = 1,
        deposit_active: bool = False,
        deposit_amount: float | None = None,
        deposit_required: bool = False,
    ) -> Service:
        with self.uow:
            service = self.uow.service_repo.create(
                profesional_id=profesional_id,
                name=name,
                duration_minutes=duration_minutes,
                price=price,
                description=description,
                max_slots=max_slots,
                deposit_active=deposit_active,
                deposit_amount=deposit_amount,
                deposit_required=deposit_required,
            )
            self.uow.commit()
            return service

    def list_services(self, profesional_id: int) -> list[Service]:
        with self.uow:
            return self.uow.service_repo.get_by_professional(profesional_id)

    def list_all_active_services(self) -> list[Service]:
        with self.uow:
            return self.uow.service_repo.get_all_active()

    def update_service(
        self,
        service_id: uuid.UUID,
        profesional_id: int,
        **fields,
    ) -> Service:
        with self.uow:
            service = self._get_own_service(service_id, profesional_id)
            self.uow.service_repo.update(service, **fields)
            self.uow.commit()
            return service

    def delete_service(
        self,
        service_id: uuid.UUID,
        profesional_id: int,
    ) -> None:
        """
        Soft-delete. Only allowed if there are no future appointments.
        """
        with self.uow:
            service = self._get_own_service(service_id, profesional_id)

            future_appointments = self.uow.appointment_repo.count_future_appointments(service_id)
            if future_appointments > 0:
                raise ServiceHasFutureAppointmentsError()

            self.uow.service_repo.soft_delete(service)
            self.uow.commit()

    def _get_own_service(self, service_id: uuid.UUID, profesional_id: int) -> Service:
        service = self.uow.service_repo.get_by_id(service_id)
        if not service:
            raise ServiceNotFoundError(str(service_id))
        if service.profesional_id != profesional_id:
            raise ServiceForbiddenError()
        return service