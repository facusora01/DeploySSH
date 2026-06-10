import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_profesional, get_service_service
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate
from app.services.services_service import ServiceService

router = APIRouter(tags=["services"])


@router.post("", summary="create a new service for a profesional",response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreate,
    current_user: User = Depends(get_current_profesional),
    service_svc: ServiceService = Depends(get_service_service),
):
    professional = current_user.profesional
    return service_svc.create_service(
        profesional_id=professional.id,
        name=payload.name,
        duration_minutes=payload.duration_minutes,
        price=payload.price,
        description=payload.description,
        max_slots=payload.max_slots,
        deposit_active=payload.deposit_active,
        deposit_amount=payload.deposit_amount,
        deposit_required=payload.deposit_required,
    )


@router.get("", summary="retrieve the list of services from a profesional",response_model=list[ServiceResponse])
def list_services(
    current_user: User = Depends(get_current_profesional),
    service_svc: ServiceService = Depends(get_service_service),
):
    professional = current_user.profesional
    return service_svc.list_services(professional.id)


@router.get("/public/available", summary="retrieve available services for clients",response_model=list[ServiceResponse])
def list_available_services(
    service_svc: ServiceService = Depends(get_service_service),
):
    return service_svc.list_all_active_services()


@router.patch("/{service_id}", summary="update a service by its ID", response_model=ServiceResponse)
def update_service(
    service_id: uuid.UUID,
    payload: ServiceUpdate,
    current_user: User = Depends(get_current_profesional),
    service_svc: ServiceService = Depends(get_service_service),
):
    professional = current_user.profesional
    return service_svc.update_service(
        service_id=service_id,
        profesional_id=professional.id,
        **payload.model_dump(exclude_unset=True),
    )


@router.delete("/{service_id}", summary="Delete a service by its ID", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: uuid.UUID,
    current_user: User = Depends(get_current_profesional),
    service_svc: ServiceService = Depends(get_service_service),
):
    professional = current_user.profesional
    service_svc.delete_service(
        service_id=service_id,
        profesional_id=professional.id,
    )
