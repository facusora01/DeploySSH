from datetime import datetime, timedelta

import pytest

from app.models.appointment import Appointment, AppointmentStatus, DepositStatus
from app.models.client import Client
from app.models.local import Local
from app.models.profesional import Profesional
from app.models.schedule_block import ScheduleBlock
from app.models.service import Service
from app.models.user import User


LOCAL_PAYLOAD = {
    "email": "local-blocks@test.com",
    "password": "strongpassword123",
    "full_name": "Admin Local",
    "role": "local",
    "phone": "+54 11 9999 0000",
    "local_name": "Local Blocks",
}


@pytest.fixture
def auth_headers_local(client, register_and_verify):
    register_and_verify(LOCAL_PAYLOAD)
    resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": LOCAL_PAYLOAD["email"],
            "password": LOCAL_PAYLOAD["password"],
        },
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def local_profile(db_session, auth_headers_local):
    user = db_session.query(User).filter(User.email == LOCAL_PAYLOAD["email"]).first()
    return db_session.query(Local).filter(Local.user_id == user.id).first()


@pytest.fixture
def team_profesional(db_session, auth_headers_profesional, local_profile):
    user = db_session.query(User).filter(User.email == "pro@test.com").first()
    prof = db_session.query(Profesional).filter(Profesional.user_id == user.id).first()
    prof.local_id = local_profile.id
    db_session.commit()
    db_session.refresh(prof)
    return prof


@pytest.fixture
def client_profile(db_session):
    user = User(
        email="client-blocks@test.com",
        password_hash="hashed_password_test",
        full_name="Client Blocks",
        phone="+54 11 5555 4444",
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
def team_service(db_session, team_profesional):
    service = Service(
        profesional_id=team_profesional.id,
        name="Servicio bloqueos",
        duration_minutes=30,
        price=100,
        max_slots=1,
        is_active=True,
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


def _appointment(db_session, service, client_profile, start_time, status):
    appointment = Appointment(
        service_id=service.id,
        client_id=client_profile.id,
        start_time=start_time,
        end_time=start_time + timedelta(minutes=service.duration_minutes),
        status=status,
        deposit_status=DepositStatus.NONE,
        notes="Turno test",
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)
    return appointment


def test_local_block_warns_then_cancels_affected_appointments(
    client,
    db_session,
    monkeypatch,
    auth_headers_local,
    team_profesional,
    team_service,
    client_profile,
):
    monkeypatch.setattr(
        "app.services.appointment_service.send_appointment_cancellation_email",
        lambda **kwargs: None,
    )

    affected = _appointment(
        db_session,
        team_service,
        client_profile,
        datetime(2026, 6, 10, 10, 0),
        AppointmentStatus.CONFIRMED,
    )
    also_affected = _appointment(
        db_session,
        team_service,
        client_profile,
        datetime(2026, 6, 11, 11, 0),
        AppointmentStatus.PENDING,
    )
    outside_range = _appointment(
        db_session,
        team_service,
        client_profile,
        datetime(2026, 6, 12, 9, 0),
        AppointmentStatus.CONFIRMED,
    )
    completed = _appointment(
        db_session,
        team_service,
        client_profile,
        datetime(2026, 6, 10, 15, 0),
        AppointmentStatus.COMPLETED,
    )

    payload = {
        "start_date": "2026-06-10",
        "end_date": "2026-06-11",
        "reason": "Cierre por mantenimiento",
    }
    preview = client.post(
        f"/api/v1/locales/me/profesionales/{team_profesional.id}/agenda/blocks",
        json=payload,
        headers=auth_headers_local,
    )

    assert preview.status_code == 409
    detail = preview.json()["detail"]
    assert detail["affected_count"] == 2
    assert {item["id"] for item in detail["appointments"]} == {
        str(affected.id),
        str(also_affected.id),
    }
    assert db_session.query(ScheduleBlock).count() == 0

    confirmed = client.post(
        f"/api/v1/locales/me/profesionales/{team_profesional.id}/agenda/blocks",
        json={**payload, "confirm_cancel_appointments": True},
        headers=auth_headers_local,
    )

    assert confirmed.status_code == 201
    body = confirmed.json()
    assert body["start_date"] == "2026-06-10"
    assert body["end_date"] == "2026-06-11"
    assert body["affected_count"] == 2
    assert body["cancelled_count"] == 2
    assert {item["id"] for item in body["cancelled_appointments"]} == {
        str(affected.id),
        str(also_affected.id),
    }

    db_session.refresh(affected)
    db_session.refresh(also_affected)
    db_session.refresh(outside_range)
    db_session.refresh(completed)
    assert affected.status == AppointmentStatus.CANCELLED
    assert also_affected.status == AppointmentStatus.CANCELLED
    assert outside_range.status == AppointmentStatus.CONFIRMED
    assert completed.status == AppointmentStatus.COMPLETED
    assert affected.cancellation_reason == (
        "Agenda bloqueada por el local: Cierre por mantenimiento"
    )


def test_local_cannot_block_profesional_outside_team(
    client,
    auth_headers_local,
    auth_headers_profesional,
    db_session,
):
    user = db_session.query(User).filter(User.email == "pro@test.com").first()
    prof = db_session.query(Profesional).filter(Profesional.user_id == user.id).first()

    response = client.post(
        f"/api/v1/locales/me/profesionales/{prof.id}/agenda/blocks",
        json={
            "start_date": "2026-06-10",
            "end_date": "2026-06-10",
            "reason": "Cierre",
            "confirm_cancel_appointments": True,
        },
        headers=auth_headers_local,
    )

    assert response.status_code == 404
