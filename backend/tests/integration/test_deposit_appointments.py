import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from app.models.service import Service
from app.models.profesional import Profesional
from app.models.weekly_schedule import WeeklySchedule
from app.models.user import User
from app.models.appointment import Appointment, AppointmentStatus, DepositStatus


@pytest.fixture
def auth_headers_client(client, register_and_verify):
    payload = {
        "email": "client@test.com",
        "password": "strongpassword123",
        "full_name": "Test Client",
        "role": "client",
        "phone": "+54 11 9876 5432"
    }
    register_and_verify(payload)
    resp = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def setup_deposit_services(db_session, auth_headers_profesional):
    """Create three services with different deposit configurations"""
    user = db_session.query(User).filter(User.email == "pro@test.com").first()
    assert user is not None

    profesional = db_session.query(Profesional).filter(Profesional.user_id == user.id).first()
    assert profesional is not None

    profesional.public_link = "pro-test-link"

    # Add weekly schedule slot
    schedule_slot = WeeklySchedule(
        profesional_id=profesional.id,
        day_of_week=0,  # Monday
        start_time="09:00:00",
        end_time="18:00:00"
    )
    db_session.add(schedule_slot)

    # Service 1: Sin seña
    service_no_deposit = Service(
        profesional_id=profesional.id,
        name="Consulta sin seña",
        description="Consulta general sin depósito",
        duration_minutes=30,
        price=Decimal("1000.00"),
        max_slots=2,
        is_active=True,
        deposit_active=False,
        deposit_amount=None,
        deposit_required=False
    )
    db_session.add(service_no_deposit)

    # Service 2: Con seña opcional
    service_optional_deposit = Service(
        profesional_id=profesional.id,
        name="Consulta con seña opcional",
        description="Consulta con depósito opcional",
        duration_minutes=30,
        price=Decimal("1000.00"),
        max_slots=2,
        is_active=True,
        deposit_active=True,
        deposit_amount=Decimal("500.00"),
        deposit_required=False
    )
    db_session.add(service_optional_deposit)

    # Service 3: Con seña obligatoria
    service_required_deposit = Service(
        profesional_id=profesional.id,
        name="Consulta con seña obligatoria",
        description="Consulta con depósito obligatorio",
        duration_minutes=30,
        price=Decimal("1000.00"),
        max_slots=2,
        is_active=True,
        deposit_active=True,
        deposit_amount=Decimal("750.00"),
        deposit_required=True
    )
    db_session.add(service_required_deposit)

    db_session.commit()
    return {
        "no_deposit": service_no_deposit,
        "optional_deposit": service_optional_deposit,
        "required_deposit": service_required_deposit
    }


def test_appointment_without_deposit(client, auth_headers_client, setup_deposit_services, db_session):
    """Test: Reservar cita sin seña debe confirmar inmediatamente"""
    service = setup_deposit_services["no_deposit"]

    # 1. Get availability
    resp_avail = client.get(f"/api/v1/availability/{service.id}")
    assert resp_avail.status_code == 200
    avail_data = resp_avail.json()
    assert avail_data["deposit_active"] == False
    assert avail_data["deposit_amount"] is None
    assert avail_data["deposit_required"] == False

    first_slot = avail_data["availability"][0]
    start_time_str = first_slot["start_time"]

    # 2. Book appointment
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time_str,
        "notes": "Cita sin seña"
    }

    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client)
    assert resp_book.status_code == 201
    book_data = resp_book.json()

    # Should be CONFIRMED immediately (no deposit required)
    assert book_data["status"] == "confirmed"
    assert book_data["deposit_status"] == "NONE"
    assert book_data["service_name"] == "Consulta sin seña"


def test_appointment_with_optional_deposit(client, auth_headers_client, setup_deposit_services, db_session):
    """Test: Reservar cita con seña opcional debe quedar PENDING"""
    service = setup_deposit_services["optional_deposit"]

    # 1. Get availability
    resp_avail = client.get(f"/api/v1/availability/{service.id}")
    assert resp_avail.status_code == 200
    avail_data = resp_avail.json()
    assert avail_data["deposit_active"] == True
    assert avail_data["deposit_amount"] == "500.00"
    assert avail_data["deposit_required"] == False

    first_slot = avail_data["availability"][0]
    start_time_str = first_slot["start_time"]

    # 2. Book appointment
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time_str,
        "notes": "Cita con seña opcional"
    }

    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client)
    assert resp_book.status_code == 201
    book_data = resp_book.json()

    # Should be PENDING with deposit_status PENDING
    assert book_data["status"] == "pending"
    assert book_data["deposit_status"] == "PENDING"
    assert book_data["service_name"] == "Consulta con seña opcional"
    appointment_id = book_data["id"]

    # 3. Client can confirm without deposit (skip optional deposit)
    resp_skip = client.patch(
        f"/api/v1/appointments/{appointment_id}/confirm-without-deposit",
        headers=auth_headers_client
    )
    assert resp_skip.status_code == 200
    confirm_data = resp_skip.json()
    # Appointment stays PENDING when skipping optional deposit
    assert confirm_data["status"] == "pending"
    assert confirm_data["deposit_status"] == "PENDING"


def test_appointment_with_required_deposit(client, auth_headers_client, setup_deposit_services, db_session):
    """Test: Reservar cita con seña obligatoria debe quedar PENDING y requerir pago"""
    service = setup_deposit_services["required_deposit"]

    # 1. Get availability
    resp_avail = client.get(f"/api/v1/availability/{service.id}")
    assert resp_avail.status_code == 200
    avail_data = resp_avail.json()
    assert avail_data["deposit_active"] == True
    assert avail_data["deposit_amount"] == "750.00"
    assert avail_data["deposit_required"] == True

    first_slot = avail_data["availability"][0]
    start_time_str = first_slot["start_time"]

    # 2. Book appointment
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time_str,
        "notes": "Cita con seña obligatoria"
    }

    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client)
    assert resp_book.status_code == 201
    book_data = resp_book.json()

    # Should be PENDING with deposit_status PENDING
    assert book_data["status"] == "pending"
    assert book_data["deposit_status"] == "PENDING"
    assert book_data["service_name"] == "Consulta con seña obligatoria"
    appointment_id = book_data["id"]

    # 3. Cannot confirm without deposit (required deposit should fail)
    resp_skip = client.patch(
        f"/api/v1/appointments/{appointment_id}/confirm-without-deposit",
        headers=auth_headers_client
    )
    # Should fail because deposit is required
    assert resp_skip.status_code == 400

    # 4. Deposit payment should succeed
    resp_deposit = client.patch(
        f"/api/v1/appointments/{appointment_id}/pay-deposit",
        headers=auth_headers_client
    )
    assert resp_deposit.status_code == 200
    deposit_data = resp_deposit.json()
    assert deposit_data["deposit_status"] == "PAID"
    assert deposit_data["status"] == "confirmed"


def test_deposit_information_in_availability(client, auth_headers_client, setup_deposit_services):
    """Test: La información de depósito aparece en el endpoint de disponibilidad"""
    services = setup_deposit_services

    for service_key, service in services.items():
        resp = client.get(f"/api/v1/availability/{service.id}")
        assert resp.status_code == 200
        data = resp.json()

        # Verify deposit fields are present
        assert "deposit_active" in data
        assert "deposit_amount" in data
        assert "deposit_required" in data

        # Verify correct values based on service
        if service_key == "no_deposit":
            assert data["deposit_active"] == False
            assert data["deposit_amount"] is None
            assert data["deposit_required"] == False
        elif service_key == "optional_deposit":
            assert data["deposit_active"] == True
            assert data["deposit_amount"] == "500.00"
            assert data["deposit_required"] == False
        elif service_key == "required_deposit":
            assert data["deposit_active"] == True
            assert data["deposit_amount"] == "750.00"
            assert data["deposit_required"] == True
