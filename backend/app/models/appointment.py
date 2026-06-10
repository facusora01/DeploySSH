import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin

class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ATTENDED = "attended"
    NO_SHOW = "no_show"

class DepositStatus(str, enum.Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    PAID = "PAID"

class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    status: Mapped[AppointmentStatus] = mapped_column(
        SQLEnum(AppointmentStatus), default=AppointmentStatus.PENDING
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    deposit_status: Mapped[DepositStatus] = mapped_column(
        SQLEnum(DepositStatus, native_enum=False), default=DepositStatus.NONE
    )

    service: Mapped["Service"] = relationship(backref="appointments")
    client: Mapped["Client"] = relationship(backref="appointments")
    form_responses: Mapped[list["FormFieldResponse"]] = relationship(
        back_populates="appointment", cascade="all, delete-orphan"
    )
    refund: Mapped["Refund | None"] = relationship(back_populates="appointment", uselist=False)

    @property
    def service_name(self) -> str:
        return self.service.name if self.service else ""

    @property
    def cliente_name(self) -> str:
        if self.client and self.client.user:
            return self.client.user.full_name
        return ""

    @property
    def cliente_phone(self) -> str | None:
        if self.client and self.client.user:
            return self.client.user.phone
        return None

    @property
    def profesional_name(self) -> str:
        if self.service and self.service.profesional and self.service.profesional.user:
            return self.service.profesional.user.full_name
        return ""

    @property
    def profesional_public_link(self) -> str:
        if self.service and self.service.profesional:
            if self.service.profesional.public_link:
                return self.service.profesional.public_link
            return str(self.service.profesional.user_id)
        return ""

    @property
    def deposit_amount(self) -> float | None:
        if self.service and self.service.deposit_active:
            return float(self.service.deposit_amount) if self.service.deposit_amount else None
        return None
