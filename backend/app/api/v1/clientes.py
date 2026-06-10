import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_cliente, get_current_profesional
from app.db.database import get_db
from app.models.appointment import Appointment
from app.models.client import Client
from app.models.client_note import ClientNote
from app.models.service import Service
from app.models.user import User
from app.schemas.cliente import (
    ClienteAppointmentHistoryItem,
    ClientePrivateNoteCreate,
    ClientePrivateNoteResponse,
    ClientePrivateNoteUpdate,
    ClienteProfessionalProfile,
    ClienteProfessionalSummary,
    ClienteResponse,
    ClienteUpdate,
)

router = APIRouter()


def _get_profesional_or_404(current_user: User):
    profesional = current_user.profesional
    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profesional profile not found",
        )
    return profesional


def _client_has_appointment_with_profesional(
    db: Session, client_id: int, profesional_id: int
) -> bool:
    return (
        db.query(Appointment.id)
        .join(Service, Appointment.service_id == Service.id)
        .filter(
            Appointment.client_id == client_id,
            Service.profesional_id == profesional_id,
        )
        .first()
        is not None
    )


def _get_accessible_client(
    db: Session, client_id: int, profesional_id: int
) -> Client:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client or not _client_has_appointment_with_profesional(
        db, client_id, profesional_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente not found",
        )
    return client


def _build_appointment_history_item(
    appointment: Appointment,
) -> ClienteAppointmentHistoryItem:
    return ClienteAppointmentHistoryItem(
        id=appointment.id,
        service_id=appointment.service_id,
        service_name=appointment.service_name,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        status=appointment.status.value,
        notes=appointment.notes,
        cancellation_reason=appointment.cancellation_reason,
    )


def _is_past_appointment(start_time: datetime, now: datetime) -> bool:
    if start_time.tzinfo is None:
        return start_time < now.replace(tzinfo=None)
    return start_time < now


@router.get("/me", response_model=ClienteResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_cliente), db: Session = Depends(get_db)
):
    cliente = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cliente profile not found"
        )

    return ClienteResponse(
        id=cliente.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        dni=cliente.dni,
        date_of_birth=cliente.date_of_birth,
        address=cliente.address,
        city=cliente.city,
        notes=cliente.notes,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.put("/me", response_model=ClienteResponse)
async def update_my_profile(
    profile_update: ClienteUpdate,
    current_user: User = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    cliente = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cliente profile not found"
        )

    # Update user fields
    if profile_update.full_name is not None:
        current_user.full_name = profile_update.full_name
    if profile_update.phone is not None:
        current_user.phone = profile_update.phone

    # Update cliente fields
    if profile_update.dni is not None:
        cliente.dni = profile_update.dni
    if profile_update.date_of_birth is not None:
        cliente.date_of_birth = profile_update.date_of_birth
    if profile_update.address is not None:
        cliente.address = profile_update.address
    if profile_update.city is not None:
        cliente.city = profile_update.city
    if profile_update.notes is not None:
        cliente.notes = profile_update.notes

    db.commit()
    db.refresh(current_user)
    db.refresh(cliente)

    return ClienteResponse(
        id=cliente.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        dni=cliente.dni,
        date_of_birth=cliente.date_of_birth,
        address=cliente.address,
        city=cliente.city,
        notes=cliente.notes,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.patch("/me", response_model=ClienteResponse)
async def partial_update_my_profile(
    profile_update: ClienteUpdate,
    current_user: User = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    return await update_my_profile(profile_update, current_user, db)


@router.get("/profesional", response_model=list[ClienteProfessionalSummary])
def list_my_clients(
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    profesional = _get_profesional_or_404(current_user)
    now = datetime.now(timezone.utc)
    appointments = (
        db.query(Appointment)
        .join(Service, Appointment.service_id == Service.id)
        .filter(Service.profesional_id == profesional.id)
        .order_by(Appointment.start_time.asc())
        .all()
    )

    summaries_by_client: dict[int, dict] = {}
    for appointment in appointments:
        client = appointment.client
        if not client or not client.user:
            continue

        summary = summaries_by_client.setdefault(
            client.id,
            {
                "id": client.id,
                "email": client.user.email,
                "full_name": client.user.full_name,
                "phone": client.user.phone,
                "last_appointment_at": None,
                "next_appointment_at": None,
                "appointments_count": 0,
                "notes_count": 0,
            },
        )
        summary["appointments_count"] += 1

        if _is_past_appointment(appointment.start_time, now):
            summary["last_appointment_at"] = appointment.start_time
        elif summary["next_appointment_at"] is None:
            summary["next_appointment_at"] = appointment.start_time

    if summaries_by_client:
        notes_counts = (
            db.query(ClientNote.client_id, ClientNote.id)
            .filter(
                ClientNote.profesional_id == profesional.id,
                ClientNote.client_id.in_(list(summaries_by_client.keys())),
            )
            .all()
        )
        for client_id, _ in notes_counts:
            summaries_by_client[client_id]["notes_count"] += 1

    return list(summaries_by_client.values())


@router.get("/{client_id}/profile", response_model=ClienteProfessionalProfile)
def get_client_profile_for_profesional(
    client_id: int,
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    profesional = _get_profesional_or_404(current_user)
    client = _get_accessible_client(db, client_id, profesional.id)

    appointments = (
        db.query(Appointment)
        .join(Service, Appointment.service_id == Service.id)
        .filter(
            Appointment.client_id == client.id,
            Service.profesional_id == profesional.id,
        )
        .order_by(Appointment.start_time.asc())
        .all()
    )
    notes = (
        db.query(ClientNote)
        .filter(
            ClientNote.client_id == client.id,
            ClientNote.profesional_id == profesional.id,
        )
        .order_by(ClientNote.created_at.asc())
        .all()
    )

    return ClienteProfessionalProfile(
        id=client.id,
        email=client.user.email,
        full_name=client.user.full_name,
        phone=client.user.phone,
        dni=client.dni,
        date_of_birth=client.date_of_birth,
        address=client.address,
        city=client.city,
        appointments=[
            _build_appointment_history_item(appointment)
            for appointment in appointments
        ],
        notes=notes,
    )


@router.post(
    "/{client_id}/notes",
    response_model=ClientePrivateNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_client_note(
    client_id: int,
    payload: ClientePrivateNoteCreate,
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    profesional = _get_profesional_or_404(current_user)
    client = _get_accessible_client(db, client_id, profesional.id)

    note = ClientNote(
        profesional_id=profesional.id,
        client_id=client.id,
        content=payload.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put(
    "/{client_id}/notes/{note_id}",
    response_model=ClientePrivateNoteResponse,
)
def update_client_note(
    client_id: int,
    note_id: uuid.UUID,
    payload: ClientePrivateNoteUpdate,
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    profesional = _get_profesional_or_404(current_user)
    _get_accessible_client(db, client_id, profesional.id)

    note = (
        db.query(ClientNote)
        .filter(
            ClientNote.id == note_id,
            ClientNote.client_id == client_id,
            ClientNote.profesional_id == profesional.id,
        )
        .first()
    )
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota not found",
        )

    note.content = payload.content
    db.commit()
    db.refresh(note)
    return note


@router.delete(
    "/{client_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_client_note(
    client_id: int,
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    profesional = _get_profesional_or_404(current_user)
    _get_accessible_client(db, client_id, profesional.id)

    note = (
        db.query(ClientNote)
        .filter(
            ClientNote.id == note_id,
            ClientNote.client_id == client_id,
            ClientNote.profesional_id == profesional.id,
        )
        .first()
    )
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nota not found",
        )

    db.delete(note)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
