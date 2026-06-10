import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Service(Base, TimestampMixin):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id"))

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    max_slots: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    deposit_active: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    deposit_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    deposit_required: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    profesional: Mapped["Profesional"] = relationship(back_populates="services")