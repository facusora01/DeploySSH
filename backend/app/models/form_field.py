import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FormField(Base, TimestampMixin):
    __tablename__ = "form_fields"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id"))
    field_name: Mapped[str] = mapped_column(String(200))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    field_type: Mapped[str] = mapped_column(String(20), default="text", server_default="text")
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)

    profesional: Mapped["Profesional"] = relationship(back_populates="form_fields")
    responses: Mapped[list["FormFieldResponse"]] = relationship(
        back_populates="field", cascade="all, delete-orphan"
    )


class FormFieldResponse(Base):
    __tablename__ = "form_field_responses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    appointment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("appointments.id"))
    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("form_fields.id"))
    answer: Mapped[str] = mapped_column(Text)

    field: Mapped["FormField"] = relationship(back_populates="responses")
    appointment: Mapped["Appointment"] = relationship(back_populates="form_responses")

    @property
    def field_name(self) -> str:
        return self.field.field_name if self.field else ""
