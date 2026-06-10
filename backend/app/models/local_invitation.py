from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.local import Local


class LocalInvitation(Base, TimestampMixin):
    """Invitation sent by a local (admin) to a professional's email.

    A professional gets linked to the local either by accepting the invitation
    while logged in (existing account) or by registering through the invitation
    link (new account). Tokens are stored hashed; the raw token travels in the
    email link only.
    """

    __tablename__ = "local_invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    local_id: Mapped[int] = mapped_column(
        ForeignKey("locales.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(255), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    # pending | accepted | cancelled  (expiry is derived from expires_at)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending"
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    local: Mapped["Local"] = relationship(back_populates="invitations")
