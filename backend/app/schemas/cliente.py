from datetime import date, datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClienteBase(BaseModel):
    dni: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None


class ClienteCreate(ClienteBase):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = None


class ClienteUpdate(ClienteBase):
    full_name: Optional[str] = Field(None, min_length=2)
    phone: Optional[str] = None


class ClienteResponse(ClienteBase):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClienteAppointmentHistoryItem(BaseModel):
    id: UUID
    service_id: UUID
    service_name: str
    start_time: datetime
    end_time: datetime
    status: str
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ClientePrivateNoteBase(BaseModel):
    content: str = Field(..., min_length=1)


class ClientePrivateNoteCreate(ClientePrivateNoteBase):
    pass


class ClientePrivateNoteUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class ClientePrivateNoteResponse(ClientePrivateNoteBase):
    id: UUID
    client_id: int
    profesional_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClienteProfessionalSummary(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    last_appointment_at: Optional[datetime] = None
    next_appointment_at: Optional[datetime] = None
    appointments_count: int
    notes_count: int


class ClienteProfessionalProfile(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    dni: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = None
    appointments: list[ClienteAppointmentHistoryItem]
    notes: list[ClientePrivateNoteResponse]

    model_config = ConfigDict(from_attributes=True)
