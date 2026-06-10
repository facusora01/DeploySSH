import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_current_profesional, get_db
from app.models.refund import Refund, RefundStatus
from app.models.appointment import Appointment
from app.models.client import Client
from app.models.user import User
from app.schemas.refund import RefundResponse

router = APIRouter()


def _build_refund_response(refund: Refund) -> RefundResponse:
    """Build RefundResponse from Refund model by flattening appointment data."""
    return RefundResponse(
        id=refund.id,
        appointment_id=refund.appointment_id,
        amount=refund.amount,
        status=refund.status.value,
        created_at=refund.created_at,
        appointment_start_time=refund.appointment.start_time,
        appointment_service_name=refund.appointment.service_name,
        appointment_client_name=refund.appointment.cliente_name,
    )


@router.get("", response_model=list[RefundResponse])
def list_refunds(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List refunds. Profesionals see refunds for their services.
    Clients see refunds for their appointments.
    """
    query = db.query(Refund).options(
        joinedload(Refund.appointment).joinedload(Appointment.service),
        joinedload(Refund.appointment).joinedload(Appointment.client),
    )

    if current_user.role == "profesional":
        profesional = current_user.profesional
        if not profesional:
            return []
        service_ids = [s.id for s in profesional.services]
        if not service_ids:
            return []
        query = query.filter(Appointment.service_id.in_(service_ids))
    else:
        # Client: filter by their appointments
        client = db.query(Client).filter(Client.user_id == current_user.id).first()
        if not client:
            return []
        query = query.join(Appointment).filter(Appointment.client_id == client.id)

    if status_filter:
        query = query.filter(Refund.status == status_filter)

    refunds = query.order_by(Refund.created_at.desc()).all()
    return [_build_refund_response(r) for r in refunds]


@router.patch("/{refund_id}/mark-done", response_model=RefundResponse)
def mark_refund_done(
    refund_id: uuid.UUID,
    current_user: User = Depends(get_current_profesional),
    db: Session = Depends(get_db),
):
    """Mark a refund as completed by the profesional."""
    refund = db.query(Refund).options(
        joinedload(Refund.appointment).joinedload(Appointment.service)
    ).filter(Refund.id == refund_id).first()

    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reembolso no encontrado",
        )

    # Only the profesional who owns the service can mark refund as done
    if refund.appointment.service.profesional.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permiso para actualizar este reembolso",
        )

    if refund.status != RefundStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este reembolso no está pendiente",
        )

    refund.status = RefundStatus.DONE

    # Notificar al cliente que el reembolso fue realizado
    from app.services.notification_service import notify_refund_done
    try:
        notify_refund_done(db, refund.appointment)
    except Exception:
        pass

    db.commit()

    return _build_refund_response(refund)
