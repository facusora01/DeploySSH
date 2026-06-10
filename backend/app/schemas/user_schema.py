from pydantic import BaseModel
from app.schemas.service import ServiceResponse
from app.schemas.agenda import WeeklyScheduleSlotOut, ScheduleBlockOut

class PublicUserProfileResponse(BaseModel):
    id: int
    full_name: str
    role: str
    phone: str | None = None
    public_link: str | None = None
    specialty: str | None = None
    bio: str | None = None
    experience_years: int | None = None
    services: list[ServiceResponse] | None = None
    weekly_schedule: list[WeeklyScheduleSlotOut] | None = None
    schedule_blocks: list[ScheduleBlockOut] | None = None

    model_config = {"from_attributes": True}
