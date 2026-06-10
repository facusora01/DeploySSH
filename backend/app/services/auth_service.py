from datetime import datetime, timezone

from app.core.config import settings
from app.core.interfaces.unit_of_work import IUnitOfWork
from app.core.security import (
    create_access_token,
    create_refresh_token,
    encode_refresh_token,
    get_password_hash,
    verify_password,
)
from app.exceptions.domain_exceptions import (
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
)
from app.models.user import User
from app.schemas.auth_schema import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.utils.email import send_reset_password_email, send_verification_email


class AuthService:
    """Service layer for authentication and token lifecycle operations."""

    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    def register(self, data: RegisterRequest) -> User:
        """Register a new user and send a verification email.

        Returns:
            User: The newly created (unverified) user.

        Raises:
            UserAlreadyExistsError: If another user already uses the same email.
        """
        if self.uow.user_repo.get_by_email(data.email):
            raise UserAlreadyExistsError(data.email)

        user = self.uow.user_repo.create_user(
            data.full_name,
            data.email,
            data.phone if data.role != "local" else None,
            get_password_hash(data.password),
            data.role,
        )

        if data.role == "profesional":
            profesional = self.uow.profesional_repo.create_profesional(
                user_id=user.id, specialty=data.specialty
            )
            if data.invitation_token:
                self._link_invitation(data.invitation_token, user.email, profesional)
        elif data.role == "local":
            self.uow.local_repo.create_local(
                user_id=user.id, local_name=data.local_name, phone=data.phone
            )
        else:
            self.uow.client_repo.create_client(user_id=user.id)

        raw_token, token_hash = create_refresh_token()
        self.uow.token_repo.create_verification_token(user.id, token_hash)

        self.uow.commit()

        send_verification_email(user.email, user.full_name, raw_token)

        return user

    def _link_invitation(self, raw_token: str, email: str, profesional) -> None:
        """Link a freshly registered professional to a local via invitation token.

        Best-effort: if the token is invalid, expired, already used, or addressed
        to a different email, registration still succeeds without linking.
        """
        invitation = self.uow.local_invitation_repo.get_by_token_hash(
            encode_refresh_token(raw_token)
        )
        if not invitation or invitation.status != "pending":
            return
        if invitation.email.lower() != email.lower():
            return

        expires_at = invitation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return

        profesional.local_id = invitation.local_id
        invitation.status = "accepted"
        invitation.accepted_at = datetime.now(timezone.utc)

    def verify_email(self, raw_token: str) -> None:
        """Mark a user's email as verified using the token from the email link.

        Raises:
            InvalidTokenError: If the token is invalid, expired, or already used.
        """
        token_hash = encode_refresh_token(raw_token)
        token = self.uow.token_repo.get_active_verification_token(token_hash)

        if not token:
            raise InvalidTokenError("El enlace de verificación es inválido o ya expiró.")

        user = self.uow.user_repo.get_by_id(token.user_id)
        user.is_email_verified = True

        self.uow.token_repo.revoke(token)
        self.uow.commit()

    def login(self, data: LoginRequest) -> tuple[User, str, str]:
        user = self.uow.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_email_verified:
            raise EmailNotVerifiedError()

        access_token = create_access_token(
            user.id, role=user.role, secret=settings.jwt_secret
        )
        refresh, refresh_hash = create_refresh_token()
        self.uow.token_repo.create(user.id, refresh_hash, user.role)
        self.uow.commit()

        return user, access_token, refresh

    def forgot_password(self, data: ForgotPasswordRequest) -> None:
        """Send a password reset email if the account exists.

        Always returns without error to avoid leaking whether the email is registered.
        """
        user = self.uow.user_repo.get_by_email(data.email)
        if not user:
            return

        raw_token, token_hash = create_refresh_token()
        self.uow.token_repo.create_reset_token(user.id, token_hash)
        self.uow.commit()

        send_reset_password_email(user.email, user.full_name, raw_token)

    def reset_password(self, data: ResetPasswordRequest) -> None:
        """Set a new password using a valid reset token.

        Raises:
            InvalidTokenError: If the token is invalid, expired, or already used.
        """
        token_hash = encode_refresh_token(data.token)
        token = self.uow.token_repo.get_active_reset_token(token_hash)

        if not token:
            raise InvalidTokenError("El enlace para restablecer la contraseña es inválido o ya expiró.")

        user = self.uow.user_repo.get_by_id(token.user_id)
        user.password_hash = get_password_hash(data.new_password)

        self.uow.token_repo.revoke(token)
        self.uow.token_repo.revoke_all_by_user_id(user.id)
        self.uow.commit()

    def logout(self, data: LogoutRequest) -> None:
        """Revoke the refresh token associated with a device."""
        refresh_token_hash = encode_refresh_token(data.refresh_token)
        token = self.uow.token_repo.get_active_refresh_token(refresh_token_hash)
        if not token:
            raise InvalidTokenError("Refresh token is invalid or expired")

        self.uow.token_repo.revoke(token)
        self.uow.commit()

    def refresh(self, data: RefreshRequest) -> tuple[str, str]:
        """Exchange a valid refresh token for a new access + refresh token pair."""
        token_hash = encode_refresh_token(data.refresh_token)
        token = self.uow.token_repo.get_active_refresh_token(token_hash)

        if not token:
            raise InvalidTokenError()

        self.uow.token_repo.revoke(token)

        access_token = create_access_token(
            token.user_id, role=token.role, secret=settings.jwt_secret
        )
        new_refresh, new_refresh_hash = create_refresh_token()
        self.uow.token_repo.create(token.user_id, new_refresh_hash, token.role)

        self.uow.commit()

        return access_token, new_refresh
