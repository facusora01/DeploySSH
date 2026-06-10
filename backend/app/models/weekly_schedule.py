import uuid
from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class WeeklySchedule(Base, TimestampMixin):
    """Una franja horaria recurrente semanal del profesional.

    Cada fila representa un bloque de trabajo en un día de la semana.
    Múltiples filas por (profesional, day_of_week) permiten partir el día
    (ej: mañana 9-13 y tarde 15-19).

    Convención: day_of_week 0=Lunes ... 6=Domingo (igual que date.weekday()).
    """

    __tablename__ = "weekly_schedules"
    __table_args__ = (
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="ck_weekly_schedules_dow_range",
        ),
        CheckConstraint(
            "start_time < end_time",
            name="ck_weekly_schedules_time_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id"))

    day_of_week: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    profesional: Mapped["Profesional"] = relationship(
        back_populates="weekly_schedule"
    )