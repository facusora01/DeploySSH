import uuid
from datetime import time

from sqlalchemy.orm import Session

from app.models.weekly_schedule import WeeklySchedule


class WeeklyScheduleRepository:
    """Repositorio de franjas horarias semanales recurrentes."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        profesional_id: int,
        day_of_week: int,
        start_time: time,
        end_time: time,
    ) -> WeeklySchedule:
        slot = WeeklySchedule(
            profesional_id=profesional_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )
        self.db.add(slot)
        return slot

    def get_by_id(self, slot_id: uuid.UUID) -> WeeklySchedule | None:
        return self.db.get(WeeklySchedule, slot_id)

    def get_by_profesional(self, profesional_id: int) -> list[WeeklySchedule]:
        """Todas las franjas del profesional, ordenadas por día y hora."""
        return (
            self.db.query(WeeklySchedule)
            .filter(WeeklySchedule.profesional_id == profesional_id)
            .order_by(WeeklySchedule.day_of_week, WeeklySchedule.start_time)
            .all()
        )

    def delete_for_profesional(self, profesional_id: int) -> None:
        """Borra todas las franjas del profesional.

        Usado por el PUT de schedule semanal, que reemplaza todo de una.
        """
        self.db.query(WeeklySchedule).filter(
            WeeklySchedule.profesional_id == profesional_id
        ).delete(synchronize_session=False)