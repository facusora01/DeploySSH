import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ScheduleBlock(Base, TimestampMixin):
    """Bloqueo de fechas del profesional (vacaciones, feriados, etc).

    Cubre tanto fechas únicas (start_date == end_date) como rangos.
    El rango es inclusivo en ambos extremos.
    """

    __tablename__ = "schedule_blocks"
    __table_args__ = (
        CheckConstraint(
            "end_date >= start_date",
            name="ck_schedule_blocks_date_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id"))

    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    profesional: Mapped["Profesional"] = relationship(
        back_populates="schedule_blocks"
    )