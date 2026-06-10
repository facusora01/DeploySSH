from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_profesional
from app.db.database import get_db
from app.models.profesional import Profesional
from app.models.user import User
from app.schemas.profesional import ProfesionalResponse, ProfesionalUpdate
from app.schemas.service import ServiceResponse

router = APIRouter()


@router.get("/me", response_model=ProfesionalResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_profesional), db: Session = Depends(get_db)
):
    profesional = (
        db.query(Profesional).filter(Profesional.user_id == current_user.id).first()
    )
    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profesional profile not found",
        )

    return ProfesionalResponse(
        id=profesional.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        specialty=profesional.specialty,
        license_number=profesional.license_number,
        experience_years=profesional.experience_years,
        bio=profesional.bio,
        consultation_fee=profesional.consultation_fee,
        is_verified=profesional.is_verified,
        services=[
            ServiceResponse.model_validate(s) for s in profesional.services if s.is_active
        ],
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.put("/me", response_model=ProfesionalResponse)
async def update_my_profile(
    profile_update: ProfesionalUpdate,
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    profesional = (
        db.query(Profesional).filter(Profesional.user_id == current_user.id).first()
    )
    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profesional profile not found",
        )

    # Update user fields
    if profile_update.full_name is not None:
        current_user.full_name = profile_update.full_name
    if profile_update.phone is not None:
        current_user.phone = profile_update.phone

    # Update profesional fields
    if profile_update.specialty is not None:
        profesional.specialty = profile_update.specialty
    if profile_update.license_number is not None:
        profesional.license_number = profile_update.license_number
    if profile_update.experience_years is not None:
        profesional.experience_years = profile_update.experience_years
    if profile_update.bio is not None:
        profesional.bio = profile_update.bio
    if profile_update.consultation_fee is not None:
        profesional.consultation_fee = profile_update.consultation_fee

    db.commit()
    db.refresh(current_user)
    db.refresh(profesional)

    return ProfesionalResponse(
        id=profesional.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        specialty=profesional.specialty,
        license_number=profesional.license_number,
        experience_years=profesional.experience_years,
        bio=profesional.bio,
        consultation_fee=profesional.consultation_fee,
        is_verified=profesional.is_verified,
        services=[
            ServiceResponse.model_validate(s) for s in profesional.services if s.is_active
        ],
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.patch("/me", response_model=ProfesionalResponse)
async def partial_update_my_profile(
    profile_update: ProfesionalUpdate,
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    return await update_my_profile(profile_update, current_user, db)
