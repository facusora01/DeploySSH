from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.user import User

if TYPE_CHECKING:
    from app.models.local import Local


class Profesional(Base, TimestampMixin):
    __tablename__ = "profesionales"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    local_id: Mapped[int | None] = mapped_column(ForeignKey("locales.id", ondelete="SET NULL"), nullable=True)
    specialty: Mapped[str] = mapped_column(String(100))  # Especialidad
    public_link: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    license_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # Matrícula
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    consultation_fee: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Configuración de agenda (US-14)
    buffer_minutes: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    agenda_paused: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    user: Mapped["User"] = relationship(back_populates="profesional")
    local: Mapped["Local | None"] = relationship(back_populates="profesionales")
    services: Mapped[list["Service"]] = relationship(
        back_populates="profesional", cascade="all, delete-orphan"
    )
    weekly_schedule: Mapped[list["WeeklySchedule"]] = relationship(
        back_populates="profesional", cascade="all, delete-orphan"
    )
    schedule_blocks: Mapped[list["ScheduleBlock"]] = relationship(
        back_populates="profesional", cascade="all, delete-orphan"
    )
    form_fields: Mapped[list["FormField"]] = relationship(
        back_populates="profesional", cascade="all, delete-orphan"
    )
    client_notes: Mapped[list["ClientNote"]] = relationship(
        back_populates="profesional", cascade="all, delete-orphan"
    )
