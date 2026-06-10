from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user_tokens import UserToken


def _refresh_expiry():
    return func.now() + timedelta(days=settings.refresh_token_expire_days)


class UserTokenRepository:
    """Persistence operations for refresh token records."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, token_hash: str, role: str) -> UserToken:
        """Create and stage a refresh token record."""
        token = UserToken(
            user_id=user_id,
            token_hash=token_hash,
            role=role,
            expires_at=_refresh_expiry(),
        )
        self.db.add(token)
        return token

    def create_verification_token(self, user_id: int, token_hash: str) -> UserToken:
        """Create and stage an email verification token record (24 h expiry)."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.email_verification_expire_hours
        )
        token = UserToken(
            user_id=user_id,
            token_hash=token_hash,
            role="email_verification",
            expires_at=expires_at,
        )
        self.db.add(token)
        return token

    def get_active_verification_token(self, token_hash: str) -> UserToken | None:
        return (
            self.db.query(UserToken)
            .filter(
                UserToken.token_hash == token_hash,
                UserToken.role == "email_verification",
                UserToken.revoked.is_(False),
                UserToken.expires_at > func.now(),
            )
            .first()
        )

    def create_reset_token(self, user_id: int, token_hash: str) -> UserToken:
        """Create and stage a password reset token (1 h expiry)."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        token = UserToken(
            user_id=user_id,
            token_hash=token_hash,
            role="password_reset",
            expires_at=expires_at,
        )
        self.db.add(token)
        return token

    def get_active_reset_token(self, token_hash: str) -> UserToken | None:
        return (
            self.db.query(UserToken)
            .filter(
                UserToken.token_hash == token_hash,
                UserToken.role == "password_reset",
                UserToken.revoked.is_(False),
                UserToken.expires_at > func.now(),
            )
            .first()
        )

    def delete(self, token: UserToken) -> None:
        """Delete a refresh token record."""
        self.db.delete(token)

    def revoke(self, token: UserToken) -> None:
        """Mark a refresh token as revoked."""
        token.revoked = True

    def revoke_all_by_user_id(self, user_id: UUID) -> int:
        """Revoke all active refresh tokens for a user."""
        return (
            self.db.query(UserToken)
            .filter(UserToken.user_id == user_id, UserToken.revoked.is_(False))
            .update({UserToken.revoked: True}, synchronize_session=False)
        )

    def get_active_refresh_token(self, refresh_token_hash: str) -> UserToken | None:
        """Retrieve a refresh token only if it is active.

        A token is considered active when it is bound to the device, not revoked,
        and not expired according to database time.
        """
        return (
            self.db.query(UserToken)
            .filter(
                UserToken.token_hash == refresh_token_hash,
                UserToken.role.notin_(["email_verification", "password_reset"]),
                UserToken.revoked.is_(False),
                UserToken.expires_at > func.now(),
            )
            .first()
        )
