import pytest
import uuid
from datetime import datetime, date
from app.models.service import Service
from app.models.profesional import Profesional
from app.models.weekly_schedule import WeeklySchedule
from app.models.user import User
from app.models.client import Client
from app.models.appointment import Appointment, AppointmentStatus, DepositStatus

@pytest.fixture
def auth_headers_client(client, register_and_verify):
    payload = {
        "email": "client_cancel@test.com",
        "password": "strongpassword123",
        "full_name": "Test Client Cancel",
        "role": "client",
        "phone": "+54 11 9876 5432"
    }
    register_and_verify(payload)
    resp = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_client_2(client, register_and_verify):
    payload = {
        "email": "client_cancel_2@test.com",
        "password": "strongpassword123",
        "full_name": "Test Client Cancel 2",
        "role": "client",
        "phone": "+54 11 9876 5433"
    }
    register_and_verify(payload)
    resp = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def setup_service(db_session, auth_headers_profesional):
    # Retrieve the professional user created by the fixture
    user = db_session.query(User).filter(User.email == "pro@test.com").first()
    assert user is not None
    
    profesional = db_session.query(Profesional).filter(Profesional.user_id == user.id).first()
    assert profesional is not None
    
    service = Service(
        profesional_id=profesional.id,
        name="Cancellation Service",
        duration_minutes=30,
        price=100.0,
        max_slots=1,
        is_active=True
    )
    db_session.add(service)
    
    schedule_slot = WeeklySchedule(
        profesional_id=profesional.id,
        day_of_week=0,
        start_time="09:00:00",
        end_time="10:00:00"
    )
    db_session.add(schedule_slot)
    
    db_session.commit()
    return service

def test_cancel_appointment_by_client(client, auth_headers_client, setup_service, db_session):
    service = setup_service
    
    start_time = datetime(2026, 6, 1, 9, 0) 
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client)
    assert resp_book.status_code == 201
    appt_id = resp_book.json()["id"]
    
    cancel_payload = {"cancellation_reason": "Client cancelled"}
    resp_cancel = client.put(f"/api/v1/appointments/{appt_id}/cancel", json=cancel_payload, headers=auth_headers_client)
    assert resp_cancel.status_code == 200
    assert resp_cancel.json()["status"] == "cancelled"
    assert resp_cancel.json()["cancellation_reason"] == "Client cancelled"
    
    appt = db_session.get(Appointment, uuid.UUID(appt_id))
    assert appt.status == AppointmentStatus.CANCELLED
    assert appt.cancellation_reason == "Client cancelled"

def test_cancel_appointment_by_professional(client, auth_headers_client, setup_service, db_session):
    service = setup_service
    
    start_time = datetime(2026, 6, 1, 9, 30)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client)
    assert resp_book.status_code == 201
    appt_id = resp_book.json()["id"]
    
    resp_pro_login = client.post("/api/v1/auth/login", json={"email": "pro@test.com", "password": "strongpassword123"})
    pro_token = resp_pro_login.json()["access_token"]
    pro_headers = {"Authorization": f"Bearer {pro_token}"}
    
    cancel_payload = {"cancellation_reason": "Professional busy"}
    resp_cancel = client.put(f"/api/v1/appointments/{appt_id}/cancel", json=cancel_payload, headers=pro_headers)
    assert resp_cancel.status_code == 200
    assert resp_cancel.json()["status"] == "cancelled"
    assert resp_cancel.json()["cancellation_reason"] == "Professional busy"

def test_cancel_appointment_by_professional_no_reason(client, auth_headers_client, setup_service, db_session):
    service = setup_service
    
    start_time = datetime(2026, 6, 1, 9, 30)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client)
    appt_id = resp_book.json()["id"]
    
    resp_pro_login = client.post("/api/v1/auth/login", json={"email": "pro@test.com", "password": "strongpassword123"})
    assert resp_pro_login.status_code == 200
    pro_token = resp_pro_login.json()["access_token"]
    pro_headers = {"Authorization": f"Bearer {pro_token}"}
    
    # Missing reason in payload (pydantic level)
    resp_cancel = client.put(f"/api/v1/appointments/{appt_id}/cancel", json={}, headers=pro_headers)
    assert resp_cancel.status_code == 422, f"Expected 422, got {resp_cancel.status_code}: {resp_cancel.text}"

    # Short reason
    resp_cancel = client.put(f"/api/v1/appointments/{appt_id}/cancel", json={"cancellation_reason": "bad"}, headers=pro_headers)
    assert resp_cancel.status_code == 422, f"Expected 422, got {resp_cancel.status_code}: {resp_cancel.text}"

def test_cancel_appointment_unauthorized(client, auth_headers_client, auth_headers_client_2, setup_service, db_session):
    service = setup_service
    
    start_time = datetime(2026, 6, 8, 9, 0)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client)
    assert resp_book.status_code == 201
    appt_id = resp_book.json()["id"]
    
    cancel_payload = {"cancellation_reason": "I want to cancel someone else's"}
    resp_cancel = client.put(f"/api/v1/appointments/{appt_id}/cancel", json=cancel_payload, headers=auth_headers_client_2)
    assert resp_cancel.status_code == 403

def test_cancel_already_cancelled_appointment(client, auth_headers_client, setup_service, db_session):
    service = setup_service
    
    start_time = datetime(2026, 6, 15, 9, 0)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client)
    appt_id = resp_book.json()["id"]
    
    cancel_payload = {"cancellation_reason": "First cancel"}
    client.put(f"/api/v1/appointments/{appt_id}/cancel", json=cancel_payload, headers=auth_headers_client)
    
    resp_cancel_again = client.put(f"/api/v1/appointments/{appt_id}/cancel", json={"cancellation_reason": "Second cancel"}, headers=auth_headers_client)
    assert resp_cancel_again.status_code == 400
    assert "ya se encuentra cancelado" in resp_cancel_again.json()["detail"]

def test_cancel_appointment_with_refund(client, auth_headers_client, setup_service, db_session, capsys):
    service = setup_service
    service.deposit_active = True
    service.deposit_amount = 50.0
    db_session.commit()
    
    start_time = datetime(2026, 6, 1, 9, 0)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client)
    appt_id = resp_book.json()["id"]
    
    # Simulate payment
    appt = db_session.get(Appointment, uuid.UUID(appt_id))
    appt.deposit_status = DepositStatus.PAID
    db_session.commit()
    
    resp_pro_login = client.post("/api/v1/auth/login", json={"email": "pro@test.com", "password": "strongpassword123"})
    pro_token = resp_pro_login.json()["access_token"]
    pro_headers = {"Authorization": f"Bearer {pro_token}"}
    
    cancel_payload = {"cancellation_reason": "Professional sick, refunding"}
    resp_cancel = client.put(f"/api/v1/appointments/{appt_id}/cancel", json=cancel_payload, headers=pro_headers)
    assert resp_cancel.status_code == 200
    
    captured = capsys.readouterr()
    assert "[MOCK REFUND] Success: Refunded 50.0" in captured.out
