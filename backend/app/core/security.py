import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id, role: str = "client", secret: str = None):
    """Create a signed access JWT for a user identifier."""
    secret = secret or settings.jwt_secret
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "role": role,
        "exp": int(
            (now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()
        ),
        "type": "access",
    }

    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)


def encode_refresh_token(token: str) -> str:
    """Encode a refresh token string as a SHA-256 hash."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token():
    """Create a random refresh token and its SHA-256 hash."""
    refresh_token = secrets.token_urlsafe(64)

    refresh_token_hash = encode_refresh_token(refresh_token)

    return refresh_token, refresh_token_hash


def decode_token(token: str, secret: str = None):
    """Decode and validate a JWT, returning None on failure."""
    secret = secret or settings.jwt_secret
    try:
        return jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
