from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class LocalBase(BaseModel):
    local_name: str
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None


class LocalCreate(LocalBase):
    pass


class LocalUpdate(BaseModel):
    local_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    opening_hours: Optional[list[dict[str, Any]]] = None


class LocalResponse(LocalBase):
    id: int
    user_id: int
    public_link: Optional[str] = None
    logo_url: Optional[str] = None
    opening_hours: Optional[list[dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Public profile schemas ────────────────────────────────────────────────────

class ServiceInLocalPublic(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    duration_minutes: int
    price: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ProfesionalInLocalPublic(BaseModel):
    id: int
    full_name: str
    specialty: str
    bio: Optional[str] = None
    public_link: Optional[str] = None
    services: list[ServiceInLocalPublic] = []

    model_config = ConfigDict(from_attributes=True)


class LocalPublicProfile(BaseModel):
    id: int
    local_name: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    opening_hours: Optional[list[dict[str, Any]]] = None
    profesionales: list[ProfesionalInLocalPublic] = []

    model_config = ConfigDict(from_attributes=True)


# ── Team invitation schemas ───────────────────────────────────────────────────

class InvitationCreate(BaseModel):
    email: EmailStr


class InvitationResponse(BaseModel):
    id: int
    email: str
    # pending | accepted | cancelled | expired
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvitationInfo(BaseModel):
    """Public details shown on the invitation acceptance page."""

    local_name: str
    email: str
    status: str
    expired: bool
    account_exists: bool
    account_is_profesional: bool


class ReceivedInvitation(BaseModel):
    """Pending invitation addressed to the logged-in professional."""

    id: int
    local_name: str
    status: str
    expires_at: datetime
    expired: bool
