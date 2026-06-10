from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_local, get_current_user, get_service_service, get_agenda_service, get_appointment_service
from app.core.config import settings
from app.core.security import create_refresh_token, encode_refresh_token
from app.db.database import get_db
from app.models.local import Local
from app.models.local_invitation import LocalInvitation
from app.models.notification import NotificationType
from app.models.appointment import Appointment, AppointmentStatus
from app.models.profesional import Profesional
from app.models.schedule_block import ScheduleBlock
from app.models.service import Service
from app.models.user import User
from app.repositories.local_invitation_repository import LocalInvitationRepository
from app.services.notification_service import create_notification
from app.utils.email import send_local_invitation_email
from app.schemas.local import (
    InvitationCreate,
    InvitationInfo,
    InvitationResponse,
    LocalPublicProfile,
    LocalResponse,
    LocalUpdate,
    ProfesionalInLocalPublic,
    ReceivedInvitation,
    ServiceInLocalPublic,
)
from app.schemas.profesional import AdminProfesionalUpdate, TeamMemberResponse, BajaPreviewItem, BajaPreviewResponse
from app.services.appointment_service import AppointmentService
from app.schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate
from app.schemas.agenda import (
    AgendaConfigResponse,
    AgendaSettingsUpdate,
    BlockedAppointmentPreview,
    TeamScheduleBlockCreate,
    TeamScheduleBlockOut,
    WeeklyScheduleUpdate,
    WeeklyScheduleSlotOut,
)
from app.services.services_service import ServiceService
from app.services.agenda_service import AgendaService
from app.exceptions.domain_exceptions import (
    ServiceHasFutureAppointmentsError,
    ScheduleBlockNotFoundError,
    ScheduleBlockForbiddenError,
    WeeklyScheduleOverlapError,
)

router = APIRouter()


def _get_local_or_404(db: Session, current_user: User) -> Local:
    local = db.query(Local).filter(Local.user_id == current_user.id).first()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Local profile not found"
        )
    return local


def _is_expired(invitation: LocalInvitation) -> bool:
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)


def _display_status(invitation: LocalInvitation) -> str:
    if invitation.status == "pending" and _is_expired(invitation):
        return "expired"
    return invitation.status


def _build_invitation_response(invitation: LocalInvitation) -> InvitationResponse:
    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        status=_display_status(invitation),
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
    )


def _notify_invited_profesional(db: Session, email: str, local_name: str) -> None:
    """If the invited email already has a professional account, drop an in-app
    notification so they get it without depending on email deliverability."""
    user = db.query(User).filter(User.email == email).first()
    if not user or user.role != "profesional":
        return
    create_notification(
        db,
        user_id=user.id,
        type=NotificationType.TEAM_INVITATION,
        title="Invitación a un equipo",
        message=f"{local_name} te invitó a sumarte a su equipo.",
    )


def _build_local_response(local: Local) -> LocalResponse:
    return LocalResponse(
        id=local.id,
        user_id=local.user_id,
        local_name=local.local_name,
        address=local.address,
        city=local.city,
        phone=local.phone,
        description=local.description,
        public_link=local.public_link,
        logo_url=local.logo_url,
        opening_hours=local.opening_hours,
        created_at=local.created_at,
        updated_at=local.updated_at,
    )


@router.get("/me", response_model=LocalResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_local), db: Session = Depends(get_db)
):
    local = db.query(Local).filter(Local.user_id == current_user.id).first()
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local profile not found")
    return _build_local_response(local)


@router.put("/me", response_model=LocalResponse)
async def update_my_profile(
    profile_update: LocalUpdate,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
):
    local = db.query(Local).filter(Local.user_id == current_user.id).first()
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local profile not found")

    for field in ("local_name", "address", "city", "phone", "description", "logo_url", "opening_hours"):
        value = getattr(profile_update, field)
        if value is not None:
            setattr(local, field, value)

    db.commit()
    db.refresh(local)
    return _build_local_response(local)


@router.patch("/me", response_model=LocalResponse)
async def partial_update_my_profile(
    profile_update: LocalUpdate,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
):
    return await update_my_profile(profile_update, current_user, db)


@router.get("/{slug}/public", response_model=LocalPublicProfile)
async def get_local_public_profile(slug: str, db: Session = Depends(get_db)):
    """Public endpoint — no auth required. Returns local profile with linked professionals."""
    local = db.query(Local).filter(Local.public_link == slug).first()
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local no encontrado")

    profesionales_data: list[ProfesionalInLocalPublic] = []
    for prof in local.profesionales:
        active_services = (
            db.query(Service)
            .filter(Service.profesional_id == prof.id, Service.is_active == True)
            .all()
        )
        services_data = [
            ServiceInLocalPublic(
                id=s.id,
                name=s.name,
                description=s.description,
                duration_minutes=s.duration_minutes,
                price=float(s.price) if s.price is not None else None,
            )
            for s in active_services
        ]
        profesionales_data.append(
            ProfesionalInLocalPublic(
                id=prof.id,
                full_name=prof.user.full_name,
                specialty=prof.specialty,
                bio=prof.bio,
                public_link=prof.public_link,
                services=services_data,
            )
        )

    return LocalPublicProfile(
        id=local.id,
        local_name=local.local_name,
        logo_url=local.logo_url,
        description=local.description,
        address=local.address,
        city=local.city,
        opening_hours=local.opening_hours,
        profesionales=profesionales_data,
    )


# ── Team invitations (US: invite professionals) ───────────────────────────────


@router.get("/me/invitations", response_model=list[InvitationResponse])
async def list_my_invitations(
    current_user: User = Depends(get_current_local), db: Session = Depends(get_db)
):
    local = _get_local_or_404(db, current_user)
    repo = LocalInvitationRepository(db)
    return [_build_invitation_response(i) for i in repo.list_by_local(local.id)]


@router.post(
    "/me/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_profesional(
    payload: InvitationCreate,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
):
    """Invite a professional to the team by email. Resends if one already exists."""
    local = _get_local_or_404(db, current_user)
    email = payload.email.strip().lower()
    repo = LocalInvitationRepository(db)

    # Solo se puede invitar profesionales. Si el email ya tiene cuenta y NO es
    # de profesional (cliente o local), no tiene sentido invitarlo: nunca podría
    # aceptar la invitación. Si no existe cuenta, se permite (se registrará como
    # profesional a través del link).
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user and existing_user.role != "profesional":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese correo pertenece a una cuenta que no es de profesional. "
            "Solo podés invitar profesionales.",
        )

    already_linked = (
        db.query(Profesional)
        .join(User, Profesional.user_id == User.id)
        .filter(User.email == email, Profesional.local_id == local.id)
        .first()
    )
    if already_linked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese profesional ya forma parte de tu equipo.",
        )

    raw_token, token_hash = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.invitation_expire_hours
    )

    invitation = repo.get_by_local_and_email(local.id, email)
    if invitation:
        invitation.token_hash = token_hash
        invitation.expires_at = expires_at
        invitation.status = "pending"
        invitation.accepted_at = None
    else:
        invitation = repo.create(local.id, email, token_hash, expires_at)

    _notify_invited_profesional(db, email, local.local_name)

    db.commit()
    db.refresh(invitation)

    send_local_invitation_email(email, local.local_name, raw_token)
    return _build_invitation_response(invitation)


@router.post(
    "/me/invitations/{invitation_id}/resend",
    response_model=InvitationResponse,
)
async def resend_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
):
    local = _get_local_or_404(db, current_user)
    repo = LocalInvitationRepository(db)
    invitation = repo.get_by_id(invitation_id)
    if not invitation or invitation.local_id != local.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitación no encontrada"
        )
    if invitation.status == "accepted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La invitación ya fue aceptada.",
        )

    raw_token, token_hash = create_refresh_token()
    invitation.token_hash = token_hash
    invitation.expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.invitation_expire_hours
    )
    invitation.status = "pending"
    invitation.accepted_at = None

    _notify_invited_profesional(db, invitation.email, local.local_name)

    db.commit()
    db.refresh(invitation)

    send_local_invitation_email(invitation.email, local.local_name, raw_token)
    return _build_invitation_response(invitation)


@router.delete(
    "/me/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def cancel_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
):
    local = _get_local_or_404(db, current_user)
    repo = LocalInvitationRepository(db)
    invitation = repo.get_by_id(invitation_id)
    if not invitation or invitation.local_id != local.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitación no encontrada"
        )
    repo.delete(invitation)
    db.commit()


def _accept_invitation(
    db: Session, invitation: LocalInvitation, current_user: User
) -> dict:
    """Shared linking logic for accepting an invitation (by token or by id)."""
    if invitation.status == "accepted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La invitación ya fue aceptada.",
        )
    if _is_expired(invitation):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La invitación expiró. Pedile al local que te reenvíe una nueva.",
        )
    if current_user.email.lower() != invitation.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta invitación fue enviada a otro correo electrónico.",
        )
    if current_user.role != "profesional":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo una cuenta de profesional puede aceptar la invitación.",
        )

    prof = (
        db.query(Profesional)
        .filter(Profesional.user_id == current_user.id)
        .first()
    )
    if not prof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró tu perfil de profesional.",
        )

    prof.local_id = invitation.local_id
    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(timezone.utc)
    db.commit()

    local = db.query(Local).filter(Local.id == invitation.local_id).first()
    return {
        "message": f"¡Listo! Ahora formás parte de {local.local_name if local else 'el local'}."
    }


def _reject_invitation(
    db: Session, invitation: LocalInvitation, current_user: User
) -> dict:
    """Shared logic for declining an invitation (by token or by id)."""
    if invitation.status == "accepted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La invitación ya fue aceptada.",
        )
    if current_user.email.lower() != invitation.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta invitación fue enviada a otro correo electrónico.",
        )
    invitation.status = "rejected"
    db.commit()
    return {"message": "Rechazaste la invitación."}


# NOTE: /invitations/received must be declared BEFORE /invitations/{token} so the
# literal "received" segment is not captured as a token.
@router.get("/invitations/received", response_model=list[ReceivedInvitation])
async def list_received_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pending invitations addressed to the logged-in professional's email."""
    invitations = (
        db.query(LocalInvitation)
        .filter(
            LocalInvitation.email == current_user.email.lower(),
            LocalInvitation.status == "pending",
        )
        .order_by(LocalInvitation.created_at.desc())
        .all()
    )
    result: list[ReceivedInvitation] = []
    for inv in invitations:
        local = db.query(Local).filter(Local.id == inv.local_id).first()
        result.append(
            ReceivedInvitation(
                id=inv.id,
                local_name=local.local_name if local else "",
                status=_display_status(inv),
                expires_at=inv.expires_at,
                expired=_is_expired(inv),
            )
        )
    return result


@router.post(
    "/invitations/received/{invitation_id}/accept",
    status_code=status.HTTP_200_OK,
)
async def accept_received_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept an invitation from the in-app notification (no token needed)."""
    repo = LocalInvitationRepository(db)
    invitation = repo.get_by_id(invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitación no encontrada"
        )
    return _accept_invitation(db, invitation, current_user)


@router.post(
    "/invitations/received/{invitation_id}/reject",
    status_code=status.HTTP_200_OK,
)
async def reject_received_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Decline an invitation from the in-app notification (no token needed)."""
    repo = LocalInvitationRepository(db)
    invitation = repo.get_by_id(invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitación no encontrada"
        )
    return _reject_invitation(db, invitation, current_user)


@router.get("/invitations/{token}", response_model=InvitationInfo)
async def get_invitation_info(token: str, db: Session = Depends(get_db)):
    """Public endpoint — used by the acceptance page to show invitation details."""
    repo = LocalInvitationRepository(db)
    invitation = repo.get_by_token_hash(encode_refresh_token(token))
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitación no encontrada"
        )

    local = db.query(Local).filter(Local.id == invitation.local_id).first()
    user = db.query(User).filter(User.email == invitation.email).first()

    return InvitationInfo(
        local_name=local.local_name if local else "",
        email=invitation.email,
        status=_display_status(invitation),
        expired=_is_expired(invitation),
        account_exists=user is not None,
        account_is_profesional=bool(user and user.role == "profesional"),
    )


@router.post("/invitations/{token}/accept", status_code=status.HTTP_200_OK)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Link the logged-in professional to the local that sent the invitation."""
    repo = LocalInvitationRepository(db)
    invitation = repo.get_by_token_hash(encode_refresh_token(token))
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitación no encontrada"
        )
    return _accept_invitation(db, invitation, current_user)


@router.post("/invitations/{token}/reject", status_code=status.HTTP_200_OK)
async def reject_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Decline the invitation that was sent to the logged-in professional."""
    repo = LocalInvitationRepository(db)
    invitation = repo.get_by_token_hash(encode_refresh_token(token))
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invitación no encontrada"
        )
    return _reject_invitation(db, invitation, current_user)


@router.post("/me/profesionales/{profesional_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_profesional_to_local(
    profesional_id: int,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
):
    local = db.query(Local).filter(Local.user_id == current_user.id).first()
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local profile not found")

    prof = db.query(Profesional).filter(Profesional.id == profesional_id).first()
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado")

    prof.local_id = local.id
    db.commit()


@router.delete("/me/profesionales/{profesional_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_profesional_from_local(
    profesional_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
    appointment_svc: AppointmentService = Depends(get_appointment_service),
):
    local = db.query(Local).filter(Local.user_id == current_user.id).first()
    if not local:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local profile not found")

    prof = db.query(Profesional).filter(
        Profesional.id == profesional_id, Profesional.local_id == local.id
    ).first()
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesional no encontrado en este local")

    service_ids = [s.id for s in prof.services]
    if service_ids:
        now = datetime.now(timezone.utc)
        future_appointments = db.query(Appointment).filter(
            Appointment.service_id.in_(service_ids),
            Appointment.start_time > now,
            Appointment.status.notin_([
                AppointmentStatus.CANCELLED,
                AppointmentStatus.COMPLETED,
                AppointmentStatus.ATTENDED,
                AppointmentStatus.NO_SHOW,
            ]),
        ).all()
        reason = "El profesional ya no forma parte del local."
        for appt in future_appointments:
            appointment_svc.cancel_by_admin(appt, reason, background_tasks)

    prof.local_id = None
    db.commit()


# ──────────── US-23: Gestión de equipo (admin) ────────────


def _get_team_profesional(profesional_id: int, local: Local, db: Session) -> Profesional:
    prof = db.query(Profesional).filter(
        Profesional.id == profesional_id,
        Profesional.local_id == local.id,
    ).first()
    if not prof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profesional no encontrado en este local",
        )
    return prof


def _build_team_member_response(prof: Profesional, db: Session):
    from app.schemas.service import ServiceResponse
    from app.schemas.profesional import TeamMemberResponse
    return TeamMemberResponse(
        id=prof.id,
        full_name=prof.user.full_name,
        email=prof.user.email,
        phone=prof.user.phone,
        specialty=prof.specialty,
        bio=prof.bio,
        photo_url=prof.photo_url,
        services=[ServiceResponse.model_validate(s) for s in prof.services if s.is_active],
    )


def _active_appointments_for_block(
    db: Session,
    prof: Profesional,
    start_date,
    end_date,
) -> list[Appointment]:
    service_ids = [s.id for s in prof.services]
    if not service_ids:
        return []

    range_start = datetime.combine(start_date, time.min)
    range_end = datetime.combine(end_date + timedelta(days=1), time.min)
    return (
        db.query(Appointment)
        .filter(
            Appointment.service_id.in_(service_ids),
            Appointment.start_time >= range_start,
            Appointment.start_time < range_end,
            Appointment.status.notin_(
                [
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.COMPLETED,
                    AppointmentStatus.ATTENDED,
                    AppointmentStatus.NO_SHOW,
                ]
            ),
        )
        .order_by(Appointment.start_time.asc())
        .all()
    )


def _build_blocked_appointment_preview(
    appointment: Appointment,
) -> BlockedAppointmentPreview:
    return BlockedAppointmentPreview(
        id=appointment.id,
        start_time=appointment.start_time,
        service_name=appointment.service.name,
        client_name=appointment.client.user.full_name,
        client_email=appointment.client.user.email,
    )


@router.get("/me/profesionales", response_model=list[TeamMemberResponse])
async def list_team(
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
):
    local = _get_local_or_404(db, current_user)
    profesionales = db.query(Profesional).filter(Profesional.local_id == local.id).all()
    return [_build_team_member_response(p, db) for p in profesionales]


@router.get("/me/profesionales/{profesional_id}", response_model=TeamMemberResponse)
async def get_team_member(
    profesional_id: int,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
):
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)
    return _build_team_member_response(prof, db)


@router.get("/me/profesionales/{profesional_id}/baja-preview", response_model=BajaPreviewResponse)
async def baja_preview(
    profesional_id: int,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
):
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)

    service_ids = [s.id for s in prof.services]
    now = datetime.now(timezone.utc)
    future_appointments: list[Appointment] = []
    if service_ids:
        future_appointments = db.query(Appointment).filter(
            Appointment.service_id.in_(service_ids),
            Appointment.start_time > now,
            Appointment.status.notin_([
                AppointmentStatus.CANCELLED,
                AppointmentStatus.COMPLETED,
                AppointmentStatus.ATTENDED,
                AppointmentStatus.NO_SHOW,
            ]),
        ).all()

    items = [
        BajaPreviewItem(
            id=str(appt.id),
            start_time=appt.start_time,
            service_name=appt.service.name,
            client_name=appt.client.user.full_name,
        )
        for appt in future_appointments
    ]
    return BajaPreviewResponse(future_count=len(items), appointments=items)


@router.patch("/me/profesionales/{profesional_id}", response_model=TeamMemberResponse)
async def update_team_member_profile(
    profesional_id: int,
    payload: AdminProfesionalUpdate,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
):
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)

    if payload.specialty is not None:
        prof.specialty = payload.specialty
    if payload.bio is not None:
        prof.bio = payload.bio
    if payload.photo_url is not None:
        prof.photo_url = payload.photo_url

    db.commit()
    db.refresh(prof)
    return _build_team_member_response(prof, db)


# ── Servicios del equipo ──

@router.get("/me/profesionales/{profesional_id}/services", response_model=list[ServiceResponse])
def list_team_services(
    profesional_id: int,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
    service_svc: ServiceService = Depends(get_service_service),
):
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)
    return service_svc.list_services(prof.id)


@router.post(
    "/me/profesionales/{profesional_id}/services",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team_service(
    profesional_id: int,
    payload: ServiceCreate,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
    service_svc: ServiceService = Depends(get_service_service),
):
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)
    return service_svc.create_service(
        profesional_id=prof.id,
        name=payload.name,
        duration_minutes=payload.duration_minutes,
        price=payload.price,
        description=payload.description,
        max_slots=payload.max_slots,
        deposit_active=payload.deposit_active,
        deposit_amount=payload.deposit_amount,
        deposit_required=payload.deposit_required,
    )


@router.patch(
    "/me/profesionales/{profesional_id}/services/{service_id}",
    response_model=ServiceResponse,
)
def update_team_service(
    profesional_id: int,
    service_id: str,
    payload: ServiceUpdate,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
    service_svc: ServiceService = Depends(get_service_service),
):
    import uuid as _uuid
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)
    return service_svc.update_service(
        service_id=_uuid.UUID(service_id),
        profesional_id=prof.id,
        **payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/me/profesionales/{profesional_id}/services/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_team_service(
    profesional_id: int,
    service_id: str,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
    service_svc: ServiceService = Depends(get_service_service),
):
    import uuid as _uuid
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)
    try:
        service_svc.delete_service(
            service_id=_uuid.UUID(service_id),
            profesional_id=prof.id,
        )
    except ServiceHasFutureAppointmentsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.details)


# ── Agenda del equipo ──

@router.get("/me/profesionales/{profesional_id}/agenda", response_model=AgendaConfigResponse)
def get_team_agenda(
    profesional_id: int,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
    agenda_svc: AgendaService = Depends(get_agenda_service),
):
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)
    return agenda_svc.get_agenda_config(prof.id)


@router.put(
    "/me/profesionales/{profesional_id}/agenda/schedule",
    response_model=list[WeeklyScheduleSlotOut],
)
def replace_team_schedule(
    profesional_id: int,
    payload: WeeklyScheduleUpdate,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
    agenda_svc: AgendaService = Depends(get_agenda_service),
):
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)
    try:
        return agenda_svc.replace_weekly_schedule(prof.id, payload.slots)
    except WeeklyScheduleOverlapError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.details)


@router.patch(
    "/me/profesionales/{profesional_id}/agenda/settings",
    status_code=status.HTTP_204_NO_CONTENT,
)
def update_team_agenda_settings(
    profesional_id: int,
    payload: AgendaSettingsUpdate,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
    agenda_svc: AgendaService = Depends(get_agenda_service),
):
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)
    agenda_svc.update_settings(prof.id, **payload.model_dump(exclude_unset=True))


@router.post(
    "/me/profesionales/{profesional_id}/agenda/blocks",
    response_model=TeamScheduleBlockOut,
    status_code=status.HTTP_201_CREATED,
)
def create_team_agenda_block(
    profesional_id: int,
    payload: TeamScheduleBlockCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
    appointment_svc: AppointmentService = Depends(get_appointment_service),
):
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)

    affected_appointments = _active_appointments_for_block(
        db,
        prof,
        payload.start_date,
        payload.end_date,
    )
    affected_preview = [
        _build_blocked_appointment_preview(appt) for appt in affected_appointments
    ]

    if affected_appointments and not payload.confirm_cancel_appointments:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": (
                    "El bloqueo afecta turnos reservados. "
                    "Confirmá la operación para cancelarlos automáticamente."
                ),
                "affected_count": len(affected_preview),
                "appointments": [
                    item.model_dump(mode="json") for item in affected_preview
                ],
            },
        )

    block = ScheduleBlock(
        profesional_id=prof.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
    )
    db.add(block)
    db.flush()

    cancellation_reason = (
        f"Agenda bloqueada por el local: {payload.reason}"
        if payload.reason
        else "Agenda bloqueada por el local."
    )
    for appointment in affected_appointments:
        appointment_svc.cancel_by_admin(
            appointment,
            cancellation_reason,
            background_tasks,
        )

    db.commit()
    db.refresh(block)

    return TeamScheduleBlockOut(
        id=block.id,
        start_date=block.start_date,
        end_date=block.end_date,
        reason=block.reason,
        affected_count=len(affected_preview),
        cancelled_count=len(affected_preview),
        cancelled_appointments=affected_preview,
    )


@router.delete(
    "/me/profesionales/{profesional_id}/agenda/blocks/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_team_agenda_block(
    profesional_id: int,
    block_id: str,
    current_user: User = Depends(get_current_local),
    db: Session = Depends(get_db),
    agenda_svc: AgendaService = Depends(get_agenda_service),
):
    import uuid as _uuid
    local = _get_local_or_404(db, current_user)
    prof = _get_team_profesional(profesional_id, local, db)
    try:
        agenda_svc.delete_block(
            block_id=_uuid.UUID(block_id),
            profesional_id=prof.id,
        )
    except (ScheduleBlockNotFoundError, ScheduleBlockForbiddenError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.details)
