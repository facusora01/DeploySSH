from abc import ABC, abstractmethod

from app.repositories.client_repository import ClientRepository
from app.repositories.profesional_repository import ProfesionalRepository
from app.repositories.local_repository import LocalRepository
from app.repositories.local_invitation_repository import LocalInvitationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_token_repository import UserTokenRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.weekly_schedule_repository import WeeklyScheduleRepository
from app.repositories.schedule_block_repository import ScheduleBlockRepository


class IUnitOfWork(ABC):
    user_repo: UserRepository
    client_repo: ClientRepository
    profesional_repo: ProfesionalRepository
    local_repo: LocalRepository
    local_invitation_repo: LocalInvitationRepository
    token_repo: UserTokenRepository
    service_repo: ServiceRepository
    appointment_repo: AppointmentRepository
    weekly_schedule_repo: WeeklyScheduleRepository
    schedule_block_repo: ScheduleBlockRepository

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *args):
        if exc_type:
            self.rollback()
        self.close()

    @abstractmethod
    def close(self) -> None: ...