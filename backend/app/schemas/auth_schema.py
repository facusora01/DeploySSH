from typing import Literal

from pydantic import (
    BaseModel,
    EmailStr,
    field_validator,
    model_validator,
)


class RegisterRequest(BaseModel):
    role: Literal["client", "profesional", "local"]
    full_name: str
    email: EmailStr
    phone: str
    password: str
    specialty: str | None = None
    local_name: str | None = None
    invitation_token: str | None = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name must not be empty")
        return v

    @field_validator("phone")
    @classmethod
    def phone_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Phone cannot be empty")
        return v

    @model_validator(mode="after")
    def validate_specialty(self) -> "RegisterRequest":
        if self.role == "profesional" and not self.specialty:
            raise ValueError("Specialty is required when registering as a profesional")
        if self.role == "local" and not self.local_name:
            raise ValueError("Local name is required when registering as a local")
        return self


class UserInAuthResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str | None = None
    public_link: str | None = None
    role: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Unified response for register and login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInAuthResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LogoutRequest(BaseModel):
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None

