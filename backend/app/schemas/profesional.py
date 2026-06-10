from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.schemas.service import ServiceResponse


class ProfesionalBase(BaseModel):
    specialty: str = Field(..., min_length=2)
    public_link: str | None = None
    license_number: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0)
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    consultation_fee: Optional[Decimal] = Field(None, ge=0)


class ProfesionalCreate(ProfesionalBase):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = None


class ProfesionalUpdate(BaseModel):
    specialty: Optional[str] = Field(None, min_length=2)
    license_number: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0)
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    consultation_fee: Optional[Decimal] = Field(None, ge=0)
    full_name: Optional[str] = Field(None, min_length=2)
    phone: Optional[str] = None


class ProfesionalResponse(ProfesionalBase):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    is_verified: bool
    services: List[ServiceResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminProfesionalUpdate(BaseModel):
    specialty: Optional[str] = Field(None, min_length=2)
    bio: Optional[str] = None
    photo_url: Optional[str] = None


class TeamMemberResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    specialty: str
    bio: Optional[str]
    photo_url: Optional[str]
    services: List[ServiceResponse] = []

    model_config = ConfigDict(from_attributes=True)


class BajaPreviewItem(BaseModel):
    id: str
    start_time: datetime
    service_name: str
    client_name: str


class BajaPreviewResponse(BaseModel):
    future_count: int
    appointments: List[BajaPreviewItem]
