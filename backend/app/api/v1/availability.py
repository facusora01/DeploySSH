import uuid
from fastapi import APIRouter, Depends
from app.api.deps import get_availability_service
from app.services.availability_service import AvailabilityService
from app.schemas.availability import ServiceAvailability

router = APIRouter(tags=["availability"])

@router.get("/{service_id}", response_model=ServiceAvailability)
def get_service_availability(
    service_id: uuid.UUID,
    availability_svc: AvailabilityService = Depends(get_availability_service)
):
    return availability_svc.get_service_availability(service_id)
