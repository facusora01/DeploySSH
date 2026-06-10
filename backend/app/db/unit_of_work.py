from sqlalchemy.orm import Session

from app.core.interfaces.unit_of_work import IUnitOfWork
from app.db.database import SessionLocal
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


class UnitOfWork(IUnitOfWork):
    def __init__(self, session: Session = None) -> None:
        self.session = session or SessionLocal()
        self._owns_session = session is None  # solo cierra si la creó él
        self.user_repo = UserRepository(self.session)
        self.client_repo = ClientRepository(self.session)
        self.profesional_repo = ProfesionalRepository(self.session)
        self.local_repo = LocalRepository(self.session)
        self.local_invitation_repo = LocalInvitationRepository(self.session)
        self.token_repo = UserTokenRepository(self.session)
        self.service_repo = ServiceRepository(self.session)
        self.appointment_repo = AppointmentRepository(self.session)
        self.weekly_schedule_repo = WeeklyScheduleRepository(self.session)
        self.schedule_block_repo = ScheduleBlockRepository(self.session)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def close(self) -> None:
        if self._owns_session:
            self.session.close()

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, *args) -> None:
        if exc_type:
            self.rollback()
        self.close()