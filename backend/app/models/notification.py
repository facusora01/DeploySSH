import uuid
import enum

from sqlalchemy import ForeignKey, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class NotificationType(str, enum.Enum):
    APPOINTMENT_BOOKED = "APPOINTMENT_BOOKED"                          # profesional: cliente tomó turno
    APPOINTMENT_CANCELLED_BY_CLIENT = "APPOINTMENT_CANCELLED_BY_CLIENT"        # profesional / local
    APPOINTMENT_CANCELLED_BY_PROFESIONAL = "APPOINTMENT_CANCELLED_BY_PROFESIONAL"  # cliente / local
    APPOINTMENT_CANCELLED_BY_LOCAL = "APPOINTMENT_CANCELLED_BY_LOCAL"          # profesional: el local canceló su turno
    REFUND_PENDING = "REFUND_PENDING"    # profesional: hay seña por devolver
    REFUND_DONE = "REFUND_DONE"          # cliente: reembolso realizado
    REMINDER = "REMINDER"                # ambos: recordatorio de turno
    TEAM_INVITATION = "TEAM_INVITATION"  # profesional: un local lo invitó a su equipo


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, native_enum=False)
    )
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(String(500))
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("appointments.id"), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    user: Mapped["User"] = relationship()
