import uuid
import enum
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RefundStatus(str, enum.Enum):
    PENDING = "PENDING"
    DONE = "DONE"


class Refund(Base, TimestampMixin):
    __tablename__ = "refunds"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    appointment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("appointments.id"), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[RefundStatus] = mapped_column(
        SQLEnum(RefundStatus, native_enum=False), default=RefundStatus.PENDING
    )

    appointment: Mapped["Appointment"] = relationship(back_populates="refund")
