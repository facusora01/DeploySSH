from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.user import User

if TYPE_CHECKING:
    from app.models.profesional import Profesional
    from app.models.local_invitation import LocalInvitation


class Local(Base, TimestampMixin):
    __tablename__ = "locales"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    local_name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_link: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    opening_hours: Mapped[list | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(backref="local")
    profesionales: Mapped[list["Profesional"]] = relationship(back_populates="local")
    invitations: Mapped[list["LocalInvitation"]] = relationship(
        back_populates="local", cascade="all, delete-orphan"
    )
