from datetime import datetime, timedelta, timezone

import pytest

from app.models.appointment import Appointment, AppointmentStatus
from app.models.client import Client
from app.models.profesional import Profesional
from app.models.service import Service
from app.models.user import User


@pytest.fixture
def client_profile(db_session):
    user = User(
        email="managed-client@test.com",
        password_hash="hashed_password_test",
        full_name="Managed Client",
        phone="+54 11 5555 4444",
        role="client",
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    profile = Client(
        user_id=user.id,
        dni="12345678",
        address="Calle Cliente 123",
        city="Buenos Aires",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def profesional_service(db_session, auth_headers_profesional):
    user = db_session.query(User).filter(User.email == "pro@test.com").first()
    profesional = db_session.query(Profesional).filter(
        Profesional.user_id == user.id
    ).first()
    service = Service(
        profesional_id=profesional.id,
        name="Consulta inicial",
        duration_minutes=30,
        price=100,
        is_active=True,
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


@pytest.fixture
def second_profesional_service(db_session, auth_headers_profesional_2):
    user = db_session.query(User).filter(User.email == "pro2@test.com").first()
    profesional = db_session.query(Profesional).filter(
        Profesional.user_id == user.id
    ).first()
    service = Service(
        profesional_id=profesional.id,
        name="Consulta pediatrica",
        duration_minutes=45,
        price=120,
        is_active=True,
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


def _create_appointment(db_session, service, client_profile, start_time, status):
    appointment = Appointment(
        service_id=service.id,
        client_id=client_profile.id,
        start_time=start_time,
        end_time=start_time + timedelta(minutes=service.duration_minutes),
        status=status,
        notes="Nota del turno",
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)
    return appointment


def test_profesional_can_view_client_profile_history_and_manage_private_notes(
    client,
    db_session,
    auth_headers_profesional,
    client_profile,
    profesional_service,
):
    past = _create_appointment(
        db_session,
        profesional_service,
        client_profile,
        datetime.now(timezone.utc) - timedelta(days=3),
        AppointmentStatus.COMPLETED,
    )
    future = _create_appointment(
        db_session,
        profesional_service,
        client_profile,
        datetime.now(timezone.utc) + timedelta(days=3),
        AppointmentStatus.CONFIRMED,
    )

    profile_response = client.get(
        f"/api/v1/clientes/{client_profile.id}/profile",
        headers=auth_headers_profesional,
    )

    assert profile_response.status_code == 200
    profile = profile_response.json()
    assert profile["id"] == client_profile.id
    assert profile["full_name"] == "Managed Client"
    assert profile["phone"] == "+54 11 5555 4444"
    assert [item["id"] for item in profile["appointments"]] == [
        str(past.id),
        str(future.id),
    ]
    assert profile["notes"] == []

    create_response = client.post(
        f"/api/v1/clientes/{client_profile.id}/notes",
        json={"content": "Prefiere turno por la mañana"},
        headers=auth_headers_profesional,
    )
    assert create_response.status_code == 201
    note = create_response.json()
    assert note["content"] == "Prefiere turno por la mañana"
    assert note["client_id"] == client_profile.id

    update_response = client.put(
        f"/api/v1/clientes/{client_profile.id}/notes/{note['id']}",
        json={"content": "Prefiere turno por la tarde"},
        headers=auth_headers_profesional,
    )
    assert update_response.status_code == 200
    assert update_response.json()["content"] == "Prefiere turno por la tarde"

    profile_with_note_response = client.get(
        f"/api/v1/clientes/{client_profile.id}/profile",
        headers=auth_headers_profesional,
    )
    assert profile_with_note_response.status_code == 200
    assert profile_with_note_response.json()["notes"][0]["content"] == (
        "Prefiere turno por la tarde"
    )

    delete_response = client.delete(
        f"/api/v1/clientes/{client_profile.id}/notes/{note['id']}",
        headers=auth_headers_profesional,
    )
    assert delete_response.status_code == 204

    final_profile_response = client.get(
        f"/api/v1/clientes/{client_profile.id}/profile",
        headers=auth_headers_profesional,
    )
    assert final_profile_response.json()["notes"] == []


def test_profesional_only_sees_own_history_and_notes(
    client,
    db_session,
    auth_headers_profesional,
    auth_headers_profesional_2,
    client_profile,
    profesional_service,
    second_profesional_service,
):
    first_pro_appointment = _create_appointment(
        db_session,
        profesional_service,
        client_profile,
        datetime.now(timezone.utc) + timedelta(days=1),
        AppointmentStatus.CONFIRMED,
    )
    second_pro_appointment = _create_appointment(
        db_session,
        second_profesional_service,
        client_profile,
        datetime.now(timezone.utc) + timedelta(days=2),
        AppointmentStatus.CONFIRMED,
    )

    first_note_response = client.post(
        f"/api/v1/clientes/{client_profile.id}/notes",
        json={"content": "Nota privada primer profesional"},
        headers=auth_headers_profesional,
    )
    assert first_note_response.status_code == 201

    second_note_response = client.post(
        f"/api/v1/clientes/{client_profile.id}/notes",
        json={"content": "Nota privada segundo profesional"},
        headers=auth_headers_profesional_2,
    )
    assert second_note_response.status_code == 201

    first_profile_response = client.get(
        f"/api/v1/clientes/{client_profile.id}/profile",
        headers=auth_headers_profesional,
    )
    second_profile_response = client.get(
        f"/api/v1/clientes/{client_profile.id}/profile",
        headers=auth_headers_profesional_2,
    )

    assert first_profile_response.status_code == 200
    assert second_profile_response.status_code == 200
    assert [item["id"] for item in first_profile_response.json()["appointments"]] == [
        str(first_pro_appointment.id)
    ]
    assert [item["id"] for item in second_profile_response.json()["appointments"]] == [
        str(second_pro_appointment.id)
    ]
    assert first_profile_response.json()["notes"][0]["content"] == (
        "Nota privada primer profesional"
    )
    assert second_profile_response.json()["notes"][0]["content"] == (
        "Nota privada segundo profesional"
    )

    forbidden_update_response = client.put(
        f"/api/v1/clientes/{client_profile.id}/notes/{first_note_response.json()['id']}",
        json={"content": "Intento de edicion cruzada"},
        headers=auth_headers_profesional_2,
    )
    assert forbidden_update_response.status_code == 404


def test_profesional_cannot_access_client_without_appointment(
    client,
    auth_headers_profesional,
    client_profile,
):
    response = client.get(
        f"/api/v1/clientes/{client_profile.id}/profile",
        headers=auth_headers_profesional,
    )

    assert response.status_code == 404
