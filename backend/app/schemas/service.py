import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    duration_minutes: int = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, ge=0)
    max_slots: int = Field(1, ge=1)
    deposit_active: bool = False
    deposit_amount: Optional[Decimal] = Field(None, ge=0)
    deposit_required: bool = False

    @model_validator(mode='after')
    def validate_deposit(self) -> 'ServiceBase':
        if self.deposit_active and (self.deposit_amount is None or self.deposit_amount <= 0):
            raise ValueError('deposit_amount must be greater than 0 when deposit_active is True')
        return self


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, ge=0)
    max_slots: Optional[int] = Field(None, ge=1)
    deposit_active: Optional[bool] = None
    deposit_amount: Optional[Decimal] = Field(None, ge=0)
    deposit_required: Optional[bool] = None

    @model_validator(mode='after')
    def validate_deposit(self) -> 'ServiceUpdate':
        if self.deposit_active is True and (self.deposit_amount is None or self.deposit_amount <= 0):
            raise ValueError('deposit_amount must be greater than 0 when deposit_active is True')
        return self


class ServiceResponse(ServiceBase):
    id: uuid.UUID
    profesional_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)