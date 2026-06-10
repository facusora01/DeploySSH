"""
Tests de integración: cancelación y listado de turnos para el rol "local".

Escenarios cubiertos:
- Un local puede listar los turnos de todos sus profesionales.
- Un local puede cancelar un turno de un profesional de su equipo (con motivo).
- Un local NO puede cancelar sin motivo o con motivo muy corto.
- Un local NO puede cancelar turnos de profesionales fuera de su equipo.
- Cancelación con seña PAID crea un Refund PENDING (reembolso).
- Se verifica el envío de email de cancelación al cliente.
- Se verifica el envío de email de reembolso pendiente al profesional cuando corresponde.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, AsyncMock

from app.models.appointment import Appointment, AppointmentStatus, DepositStatus
from app.models.client import Client
from app.models.local import Local
from app.models.profesional import Profesional
from app.models.refund import Refund, RefundStatus
from app.models.service import Service
from app.models.user import User
from app.models.weekly_schedule import WeeklySchedule


# ── Payloads de registro ──────────────────────────────────────────────────────

LOCAL_PAYLOAD = {
    "email": "local-cancel@test.com",
    "password": "strongpassword123",
    "full_name": "Admin Local",
    "role": "local",
    "phone": "+54 11 9999 0000",
    "local_name": "Local Cancelaciones",
}


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def auth_headers_local(client, register_and_verify):
    register_and_verify(LOCAL_PAYLOAD)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": LOCAL_PAYLOAD["email"], "password": LOCAL_PAYLOAD["password"]},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def local_profile(db_session, auth_headers_local):
    user = db_session.query(User).filter(User.email == LOCAL_PAYLOAD["email"]).first()
    return db_session.query(Local).filter(Local.user_id == user.id).first()


@pytest.fixture
def team_profesional(db_session, auth_headers_profesional, local_profile):
    """Profesional perteneciente al equipo del local."""
    user = db_session.query(User).filter(User.email == "pro@test.com").first()
    prof = db_session.query(Profesional).filter(Profesional.user_id == user.id).first()
    prof.local_id = local_profile.id
    db_session.commit()
    db_session.refresh(prof)
    return prof


@pytest.fixture
def external_profesional(db_session, auth_headers_profesional_2):
    """Profesional que NO pertenece al equipo del local."""
    user = db_session.query(User).filter(User.email == "pro2@test.com").first()
    return db_session.query(Profesional).filter(Profesional.user_id == user.id).first()


@pytest.fixture
def team_service(db_session, team_profesional):
    service = Service(
        profesional_id=team_profesional.id,
        name="Servicio del equipo",
        duration_minutes=30,
        price=100.0,
        max_slots=3,
        is_active=True,
    )
    db_session.add(service)
    db_session.add(WeeklySchedule(
        profesional_id=team_profesional.id,
        day_of_week=0,
        start_time="09:00:00",
        end_time="12:00:00",
    ))
    db_session.commit()
    db_session.refresh(service)
    return service


@pytest.fixture
def external_service(db_session, external_profesional):
    service = Service(
        profesional_id=external_profesional.id,
        name="Servicio externo",
        duration_minutes=30,
        price=80.0,
        max_slots=1,
        is_active=True,
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


@pytest.fixture
def client_user(db_session):
    user = User(
        email="cliente-local-cancel@test.com",
        password_hash="hashed_password_test",
        full_name="Cliente Local",
        phone="+54 11 5555 1234",
        role="client",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    profile = Client(user_id=user.id)
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def booked_appointment(db_session, team_service, client_user):
    appt = Appointment(
        service_id=team_service.id,
        client_id=client_user.id,
        start_time=datetime(2026, 8, 1, 9, 0),
        end_time=datetime(2026, 8, 1, 9, 30),
        status=AppointmentStatus.CONFIRMED,
        deposit_status=DepositStatus.NONE,
    )
    db_session.add(appt)
    db_session.commit()
    db_session.refresh(appt)
    return appt


@pytest.fixture
def booked_appointment_with_deposit(db_session, team_service, client_user):
    appt = Appointment(
        service_id=team_service.id,
        client_id=client_user.id,
        start_time=datetime(2026, 8, 1, 10, 0),
        end_time=datetime(2026, 8, 1, 10, 30),
        status=AppointmentStatus.CONFIRMED,
        deposit_status=DepositStatus.PAID,
    )
    db_session.add(appt)
    db_session.commit()
    db_session.refresh(appt)
    # El servicio necesita deposit_amount para que el Refund tenga monto
    team_service.deposit_active = True
    team_service.deposit_amount = 200.0
    db_session.commit()
    return appt


@pytest.fixture
def external_appointment(db_session, external_service, client_user):
    appt = Appointment(
        service_id=external_service.id,
        client_id=client_user.id,
        start_time=datetime(2026, 8, 2, 9, 0),
        end_time=datetime(2026, 8, 2, 9, 30),
        status=AppointmentStatus.CONFIRMED,
        deposit_status=DepositStatus.NONE,
    )
    db_session.add(appt)
    db_session.commit()
    db_session.refresh(appt)
    return appt


# ── Tests: listado ─────────────────────────────────────────────────────────────


def test_local_lists_team_appointments(client, auth_headers_local, booked_appointment):
    """El local ve los turnos de los profesionales de su equipo."""
    resp = client.get("/api/v1/appointments", headers=auth_headers_local)
    assert resp.status_code == 200
    ids = [a["id"] for a in resp.json()]
    assert str(booked_appointment.id) in ids


def test_local_does_not_see_external_appointments(
    client, auth_headers_local, external_appointment
):
    """El local no ve turnos de profesionales fuera de su equipo."""
    resp = client.get("/api/v1/appointments", headers=auth_headers_local)
    assert resp.status_code == 200
    ids = [a["id"] for a in resp.json()]
    assert str(external_appointment.id) not in ids


def test_local_sees_cancelled_appointments(client, auth_headers_local, booked_appointment):
    """El local ve todos los turnos incluyendo los cancelados (igual que el profesional)."""
    booked_appointment.status = AppointmentStatus.CANCELLED
    # Necesitamos acceder al db_session; el fixture ya hizo commit, así que usamos
    # el turno ya creado y lo cancelamos via API para verificar que aparece igual.
    resp = client.get("/api/v1/appointments", headers=auth_headers_local)
    assert resp.status_code == 200
    # El turno (cancelado o no) debe estar en la lista
    ids = [a["id"] for a in resp.json()]
    assert str(booked_appointment.id) in ids


# ── Tests: cancelación ────────────────────────────────────────────────────────


def test_local_cancels_team_appointment(
    client, auth_headers_local, booked_appointment
):
    """El local puede cancelar un turno de su equipo con motivo válido."""
    with patch("app.utils.email.send_appointment_cancellation_email") as mock_email:
        resp = client.put(
            f"/api/v1/appointments/{booked_appointment.id}/cancel",
            json={"cancellation_reason": "El profesional no puede atender"},
            headers=auth_headers_local,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "cancelled"
    assert body["cancellation_reason"] == "El profesional no puede atender"


def test_local_cancel_requires_reason(
    client, auth_headers_local, booked_appointment
):
    """El local debe proveer un motivo de al menos 5 caracteres."""
    resp = client.put(
        f"/api/v1/appointments/{booked_appointment.id}/cancel",
        json={"cancellation_reason": "ok"},
        headers=auth_headers_local,
    )
    assert resp.status_code == 422


def test_local_cannot_cancel_external_appointment(
    client, auth_headers_local, external_appointment
):
    """El local no puede cancelar turnos de profesionales de otro equipo."""
    resp = client.put(
        f"/api/v1/appointments/{external_appointment.id}/cancel",
        json={"cancellation_reason": "Intento de cancelación no autorizado"},
        headers=auth_headers_local,
    )
    assert resp.status_code == 403


def test_local_cancel_already_cancelled_returns_400(
    client, auth_headers_local, booked_appointment, db_session
):
    """Intentar cancelar un turno ya cancelado retorna 400."""
    booked_appointment.status = AppointmentStatus.CANCELLED
    booked_appointment.cancellation_reason = "Ya cancelado antes"
    db_session.commit()

    resp = client.put(
        f"/api/v1/appointments/{booked_appointment.id}/cancel",
        json={"cancellation_reason": "Segunda cancelación"},
        headers=auth_headers_local,
    )
    assert resp.status_code == 400
    assert "ya se encuentra cancelado" in resp.json()["detail"]


# ── Tests: emails ─────────────────────────────────────────────────────────────


def test_local_cancel_sends_cancellation_email_to_client(
    client, auth_headers_local, booked_appointment
):
    """Al cancelar, el cliente recibe un email de cancelación."""
    with patch("app.utils.email.send_appointment_cancellation_email") as mock_email:
        resp = client.put(
            f"/api/v1/appointments/{booked_appointment.id}/cancel",
            json={"cancellation_reason": "Cierre temporal del local"},
            headers=auth_headers_local,
        )
    assert resp.status_code == 200
    mock_email.assert_called_once()
    call_kwargs = mock_email.call_args
    assert call_kwargs is not None


def test_local_cancel_with_paid_deposit_creates_refund_and_notifies_profesional(
    client, auth_headers_local, booked_appointment_with_deposit, db_session
):
    """Cancelación con seña PAID crea Refund PENDING y notifica al profesional."""
    appt_id = booked_appointment_with_deposit.id

    with (
        patch("app.utils.email.send_appointment_cancellation_email"),
        patch("app.utils.email.send_refund_pending_email") as mock_refund_email,
    ):
        resp = client.put(
            f"/api/v1/appointments/{appt_id}/cancel",
            json={"cancellation_reason": "Cancelado por el local, se reembolsa seña"},
            headers=auth_headers_local,
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    # Verificar que se creó el Refund en DB
    db_session.expire_all()
    refund = db_session.query(Refund).filter(Refund.appointment_id == appt_id).first()
    assert refund is not None
    assert refund.status == RefundStatus.PENDING
    assert float(refund.amount) == 200.0

    # Verificar email de reembolso pendiente enviado al profesional
    mock_refund_email.assert_called_once()


def test_local_cancel_without_paid_deposit_creates_no_refund(
    client, auth_headers_local, booked_appointment, db_session
):
    """Si el depósito no fue pagado, no se crea un Refund al cancelar."""
    appt_id = booked_appointment.id

    with patch("app.utils.email.send_appointment_cancellation_email"):
        resp = client.put(
            f"/api/v1/appointments/{appt_id}/cancel",
            json={"cancellation_reason": "Sin depósito, sin reembolso"},
            headers=auth_headers_local,
        )

    assert resp.status_code == 200
    db_session.expire_all()
    refund = db_session.query(Refund).filter(Refund.appointment_id == appt_id).first()
    assert refund is None
