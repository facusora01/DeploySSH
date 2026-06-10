import uuid

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_agenda_service, get_current_profesional
from app.models.user import User
from app.schemas.agenda import (
    AgendaConfigResponse,
    AgendaSettingsUpdate,
    ScheduleBlockCreate,
    ScheduleBlockOut,
    WeeklyScheduleSlotOut,
    WeeklyScheduleUpdate,
)
from app.services.agenda_service import AgendaService

router = APIRouter(tags=["agenda"])


@router.get(
    "",
    summary="Get the full agenda config of the logged-in profesional",
    response_model=AgendaConfigResponse,
)
def get_agenda_config(
    current_user: User = Depends(get_current_profesional),
    agenda_svc: AgendaService = Depends(get_agenda_service),
):
    professional = current_user.profesional
    return agenda_svc.get_agenda_config(professional.id)


@router.put(
    "/schedule",
    summary="Replace the weekly schedule of the logged-in profesional",
    response_model=list[WeeklyScheduleSlotOut],
)
def replace_weekly_schedule(
    payload: WeeklyScheduleUpdate,
    current_user: User = Depends(get_current_profesional),
    agenda_svc: AgendaService = Depends(get_agenda_service),
):
    professional = current_user.profesional
    return agenda_svc.replace_weekly_schedule(
        profesional_id=professional.id,
        slots=payload.slots,
    )


@router.post(
    "/blocks",
    summary="Create a schedule block (vacation, holiday, day off)",
    response_model=ScheduleBlockOut,
    status_code=status.HTTP_201_CREATED,
)
def create_block(
    payload: ScheduleBlockCreate,
    current_user: User = Depends(get_current_profesional),
    agenda_svc: AgendaService = Depends(get_agenda_service),
):
    professional = current_user.profesional
    return agenda_svc.create_block(
        profesional_id=professional.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
    )


@router.delete(
    "/blocks/{block_id}",
    summary="Delete a schedule block by its ID",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_block(
    block_id: uuid.UUID,
    current_user: User = Depends(get_current_profesional),
    agenda_svc: AgendaService = Depends(get_agenda_service),
):
    professional = current_user.profesional
    agenda_svc.delete_block(
        block_id=block_id,
        profesional_id=professional.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/settings",
    summary="Update buffer_minutes and/or agenda_paused",
    status_code=status.HTTP_204_NO_CONTENT,
)
def update_settings(
    payload: AgendaSettingsUpdate,
    current_user: User = Depends(get_current_profesional),
    agenda_svc: AgendaService = Depends(get_agenda_service),
):
    professional = current_user.profesional
    # exclude_unset=True: solo pasamos los campos que el cliente mandó
    # explícitamente. Si solo vino agenda_paused, buffer_minutes ni siquiera
    # se intenta tocar.
    agenda_svc.update_settings(
        profesional_id=professional.id,
        **payload.model_dump(exclude_unset=True),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)