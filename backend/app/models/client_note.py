import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ClientNote(Base, TimestampMixin):
    __tablename__ = "client_notes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id"))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    content: Mapped[str] = mapped_column(Text)

    profesional: Mapped["Profesional"] = relationship(back_populates="client_notes")
    client: Mapped["Client"] = relationship(back_populates="private_notes")
