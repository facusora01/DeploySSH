from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional

from app.schemas.form_field import FormFieldAnswerCreate, FormFieldAnswerOut


class AppointmentCreate(BaseModel):
    service_id: UUID
    start_time: datetime
    notes: Optional[str] = None

    # Optional profile updates
    full_name: Optional[str] = None
    phone: Optional[str] = None
    dni: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = None

    # Custom form field responses
    form_responses: list[FormFieldAnswerCreate] = []


class AppointmentAttendanceUpdate(BaseModel):
    status: Literal["attended", "no_show"]


class AppointmentCancel(BaseModel):
    cancellation_reason: str = Field(..., min_length=5)


class AppointmentResponse(BaseModel):
    id: UUID
    service_id: UUID
    client_id: int
    start_time: datetime
    end_time: datetime
    status: str
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    deposit_status: str
    deposit_amount: Optional[Decimal] = None

    # Nested fields resolved via model properties
    service_name: str
    cliente_name: str
    cliente_phone: Optional[str]
    profesional_name: str
    profesional_public_link: str

    # Custom form field responses (populated for professional view)
    form_responses: list[FormFieldAnswerOut] = []

    model_config = ConfigDict(from_attributes=True)
