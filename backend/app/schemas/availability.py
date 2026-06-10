from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class SlotAvailability(BaseModel):
    start_time: datetime
    end_time: datetime
    max_slots: int
    current_occupancy: int
    is_available: bool

class ServiceAvailability(BaseModel):
    service_id: UUID
    service_name: str
    profesional_public_link: str
    availability: list[SlotAvailability]
    deposit_active: bool = False
    deposit_amount: Optional[Decimal] = None
    deposit_required: bool = False
