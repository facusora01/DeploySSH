from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class RefundResponse(BaseModel):
    id: UUID
    appointment_id: UUID
    amount: Decimal
    status: str
    created_at: datetime
    # Nested appointment fields for listing
    appointment_start_time: datetime
    appointment_service_name: str
    appointment_client_name: str

    model_config = ConfigDict(from_attributes=True)
