"""Helpers para crear notificaciones in-app.

Las funciones agregan la Notification a la sesion provista pero NO hacen commit
(salvo que se pase commit=True). El caller decide cuando persistir, lo que permite
incluirlas dentro de la misma transaccion del flujo que las origina.
"""
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.notification import Notification, NotificationType


def _fmt(dt) -> str:
    return dt.strftime("%d/%m/%Y %H:%M") if dt else ""


def create_notification(
    db: Session,
    *,
    user_id: int,
    type: NotificationType,
    title: str,
    message: str,
    appointment_id=None,
    commit: bool = False,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        appointment_id=appointment_id,
    )
    db.add(notif)
    if commit:
        db.commit()
    return notif


# --- Helpers ---

def _local_user_id(appointment: Appointment) -> int | None:
    """Devuelve el user_id del local si el profesional pertenece a uno, sino None."""
    local = appointment.service.profesional.local
    return local.user_id if local else None


# --- Builders por evento ---

def notify_appointment_booked(db: Session, appointment: Appointment, *, commit: bool = False):
    """Profesional: un cliente tomó un turno."""
    profesional_user_id = appointment.service.profesional.user_id
    return create_notification(
        db,
        user_id=profesional_user_id,
        type=NotificationType.APPOINTMENT_BOOKED,
        title="Nuevo turno reservado",
        message=f"{appointment.cliente_name} reservó {appointment.service_name} para el {_fmt(appointment.start_time)}.",
        appointment_id=appointment.id,
        commit=commit,
    )


def notify_appointment_cancelled_by_client(db: Session, appointment: Appointment, *, commit: bool = False):
    """Profesional: un cliente canceló su turno. Si el profesional pertenece a un local, también notifica al local."""
    profesional_user_id = appointment.service.profesional.user_id
    create_notification(
        db,
        user_id=profesional_user_id,
        type=NotificationType.APPOINTMENT_CANCELLED_BY_CLIENT,
        title="Turno cancelado",
        message=f"{appointment.cliente_name} canceló {appointment.service_name} del {_fmt(appointment.start_time)}.",
        appointment_id=appointment.id,
    )
    local_uid = _local_user_id(appointment)
    if local_uid:
        create_notification(
            db,
            user_id=local_uid,
            type=NotificationType.APPOINTMENT_CANCELLED_BY_CLIENT,
            title="Turno cancelado",
            message=f"{appointment.cliente_name} canceló {appointment.service_name} con {appointment.profesional_name} del {_fmt(appointment.start_time)}.",
            appointment_id=appointment.id,
        )
    if commit:
        db.commit()


def notify_appointment_cancelled_by_profesional(db: Session, appointment: Appointment, *, commit: bool = False):
    """Cliente: el profesional canceló su turno. Si el profesional pertenece a un local, también notifica al local."""
    client_user_id = appointment.client.user_id
    create_notification(
        db,
        user_id=client_user_id,
        type=NotificationType.APPOINTMENT_CANCELLED_BY_PROFESIONAL,
        title="Turno cancelado",
        message=f"{appointment.profesional_name} canceló tu turno de {appointment.service_name} del {_fmt(appointment.start_time)}.",
        appointment_id=appointment.id,
    )
    local_uid = _local_user_id(appointment)
    if local_uid:
        create_notification(
            db,
            user_id=local_uid,
            type=NotificationType.APPOINTMENT_CANCELLED_BY_PROFESIONAL,
            title="Turno cancelado",
            message=f"{appointment.profesional_name} canceló {appointment.service_name} con {appointment.cliente_name} del {_fmt(appointment.start_time)}.",
            appointment_id=appointment.id,
        )
    if commit:
        db.commit()


def notify_appointment_cancelled_by_local(db: Session, appointment: Appointment, *, commit: bool = False):
    """Profesional: el local canceló su turno."""
    profesional_user_id = appointment.service.profesional.user_id
    local_name = appointment.service.profesional.local.local_name
    create_notification(
        db,
        user_id=profesional_user_id,
        type=NotificationType.APPOINTMENT_CANCELLED_BY_LOCAL,
        title="Turno cancelado",
        message=f"{local_name} canceló tu turno de {appointment.service_name} con {appointment.cliente_name} del {_fmt(appointment.start_time)}.",
        appointment_id=appointment.id,
        commit=commit,
    )


def notify_refund_pending(db: Session, appointment: Appointment, *, commit: bool = False):
    """Profesional: hay una seña por devolver."""
    profesional_user_id = appointment.service.profesional.user_id
    return create_notification(
        db,
        user_id=profesional_user_id,
        type=NotificationType.REFUND_PENDING,
        title="Reembolso pendiente",
        message=f"Tenés que devolver la seña de {appointment.cliente_name} por {appointment.service_name} del {_fmt(appointment.start_time)}.",
        appointment_id=appointment.id,
        commit=commit,
    )


def notify_refund_done(db: Session, appointment: Appointment, *, commit: bool = False):
    """Cliente: el reembolso fue realizado."""
    client_user_id = appointment.client.user_id
    return create_notification(
        db,
        user_id=client_user_id,
        type=NotificationType.REFUND_DONE,
        title="Reembolso realizado",
        message=f"Se procesó el reembolso de tu seña por {appointment.service_name} del {_fmt(appointment.start_time)}.",
        appointment_id=appointment.id,
        commit=commit,
    )


def notify_reminder(db: Session, user_id: int, appointment: Appointment, *, for_client: bool, commit: bool = False):
    """Recordatorio de turno proximo (cliente o profesional)."""
    if for_client:
        message = f"Tu turno de {appointment.service_name} es a las {_fmt(appointment.start_time)}."
    else:
        message = f"Turno con {appointment.cliente_name} ({appointment.service_name}) a las {_fmt(appointment.start_time)}."
    return create_notification(
        db,
        user_id=user_id,
        type=NotificationType.REMINDER,
        title="Recordatorio de turno",
        message=message,
        appointment_id=appointment.id,
        commit=commit,
    )
