from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.profesional import Profesional
from app.models.service import Service
from app.models.weekly_schedule import WeeklySchedule
from app.models.schedule_block import ScheduleBlock
from app.schemas.auth_schema import UserInAuthResponse, UserUpdateRequest
from app.schemas.user_schema import PublicUserProfileResponse

router = APIRouter()

@router.put("/me", response_model=UserInAuthResponse)
def update_user_me(
    data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update own user profile.
    """
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.phone is not None:
        current_user.phone = data.phone

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/{identifier}/public", response_model=PublicUserProfileResponse)
def get_public_profile(identifier: str, db: Session = Depends(get_db)):
    """
    Get public profile of any user.
    """
    target_user = None
    if identifier.isdigit():
        target_user = db.query(User).filter(User.id == int(identifier)).first()
    if not target_user:
        target_user = (
            db.query(User)
            .join(Profesional)
            .filter(Profesional.public_link == identifier)
            .first()
        )
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    response = PublicUserProfileResponse(
        id=target_user.id,
        full_name=target_user.full_name,
        role=target_user.role,
        phone=target_user.phone,
    )
    
    # Si es profesional, sacamos info extra
    if target_user.role == "profesional" and target_user.profesional:
        prof = target_user.profesional
        response.specialty = prof.specialty
        response.bio = prof.bio
        response.experience_years = prof.experience_years
        response.public_link = prof.public_link
        # incluir servicios publicados activos
        services = (
            db.query(Service)
            .filter(Service.profesional_id == prof.id, Service.is_active == True)
            .all()
        )
        response.services = services

        weekly_schedule = (
            db.query(WeeklySchedule)
            .filter(WeeklySchedule.profesional_id == prof.id)
            .order_by(WeeklySchedule.day_of_week, WeeklySchedule.start_time)
            .all()
        )
        schedule_blocks = (
            db.query(ScheduleBlock)
            .filter(ScheduleBlock.profesional_id == prof.id)
            .order_by(ScheduleBlock.start_date)
            .all()
        )
        response.weekly_schedule = weekly_schedule
        response.schedule_blocks = schedule_blocks
        
    return response
