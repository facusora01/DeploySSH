import pytest
from datetime import datetime, date, timedelta
from app.models.service import Service
from app.models.profesional import Profesional
from app.models.weekly_schedule import WeeklySchedule
from app.models.user import User
from app.models.client import Client
from app.models.appointment import Appointment, AppointmentStatus

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
def setup_service(db_session, auth_headers_profesional):
    # Retrieve the professional user created by the fixture
    user = db_session.query(User).filter(User.email == "pro@test.com").first()
    assert user is not None
    
    profesional = db_session.query(Profesional).filter(Profesional.user_id == user.id).first()
    assert profesional is not None
    
    # Set unique public link
    profesional.public_link = "pro-test-link"
    
    # Add a service
    service = Service(
        profesional_id=profesional.id,
        name="Test Dermatology Service",
        description="A cool service",
        duration_minutes=30,
        price=150.0,
        max_slots=2,
        is_active=True
    )
    db_session.add(service)
    
    # Add a weekly schedule slot
    schedule_slot = WeeklySchedule(
        profesional_id=profesional.id,
        day_of_week=0,  # Monday
        start_time="09:00:00",
        end_time="12:00:00"
    )
    db_session.add(schedule_slot)
    
    db_session.commit()
    return service

def test_create_and_list_appointments(client, auth_headers_client, setup_service, db_session):
    service = setup_service
    
    # 1. Get service availability
    resp_avail = client.get(f"/api/v1/availability/{service.id}")
    assert resp_avail.status_code == 200
    avail_data = resp_avail.json()
    assert avail_data["service_name"] == "Test Dermatology Service"
    assert len(avail_data["availability"]) > 0
    
    # Pick the first available slot
    first_slot = avail_data["availability"][0]
    start_time_str = first_slot["start_time"]
    
    # 2. Book appointment with optional profile pre-fills
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time_str,
        "notes": "Please be on time",
        "full_name": "Updated Client Name",
        "phone": "+54 9 11 9999 8888",
        "dni": "12345678A",
        "date_of_birth": "1995-10-15",
        "address": "Av. Siempreviva 742",
        "city": "Springfield"
    }
    
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client)
    assert resp_book.status_code == 201
    book_data = resp_book.json()
    assert book_data["status"] == "confirmed"
    assert book_data["notes"] == "Please be on time"
    assert book_data["service_name"] == "Test Dermatology Service"
    assert book_data["cliente_name"] == "Updated Client Name"
    assert book_data["cliente_phone"] == "+54 9 11 9999 8888"
    assert book_data["profesional_name"] == "Test Pro"
    assert book_data["profesional_public_link"] == "pro-test-link"
    
    # Verify client profile database records were updated
    client_user = db_session.query(User).filter(User.email == "client@test.com").first()
    assert client_user.full_name == "Updated Client Name"
    assert client_user.phone == "+54 9 11 9999 8888"
    
    client_profile = db_session.query(Client).filter(Client.user_id == client_user.id).first()
    assert client_profile.dni == "12345678A"
    assert client_profile.date_of_birth == date(1995, 10, 15)
    assert client_profile.address == "Av. Siempreviva 742"
    assert client_profile.city == "Springfield"
    
    # 3. List appointments as client
    resp_client_list = client.get("/api/v1/appointments", headers=auth_headers_client)
    assert resp_client_list.status_code == 200
    client_list = resp_client_list.json()
    assert len(client_list) == 1
    assert client_list[0]["cliente_name"] == "Updated Client Name"
    assert client_list[0]["profesional_public_link"] == "pro-test-link"
    
    # 4. List appointments as professional
    # Login as professional using auth_headers_profesional
    from conftest import auth_headers_profesional
    pro_user = db_session.query(User).filter(User.email == "pro@test.com").first()
    resp_pro_login = client.post("/api/v1/auth/login", json={"email": "pro@test.com", "password": "strongpassword123"})
    pro_token = resp_pro_login.json()["access_token"]
    pro_headers = {"Authorization": f"Bearer {pro_token}"}
    
    resp_pro_list = client.get("/api/v1/appointments", headers=pro_headers)
    assert resp_pro_list.status_code == 200
    pro_list = resp_pro_list.json()
    assert len(pro_list) == 1
    assert pro_list[0]["cliente_name"] == "Updated Client Name"

def test_booking_exceeds_max_slots(client, auth_headers_client, setup_service, db_session, register_and_verify):
    service = setup_service
    
    # Fetch availability to get a valid time slot
    resp_avail = client.get(f"/api/v1/availability/{service.id}")
    assert resp_avail.status_code == 200
    avail_data = resp_avail.json()
    start_time_str = avail_data["availability"][0]["start_time"]
    
    # Create an appointment for Client 1
    booking_payload_1 = {
        "service_id": str(service.id),
        "start_time": start_time_str
    }
    resp_book_1 = client.post("/api/v1/appointments", json=booking_payload_1, headers=auth_headers_client)
    assert resp_book_1.status_code == 201
    
    # Create another client to book the second slot (max_slots is 2)
    payload_client_2 = {
        "email": "client2@test.com",
        "password": "strongpassword123",
        "full_name": "Second Client",
        "role": "client",
        "phone": "+54 11 9876 5433"
    }
    register_and_verify(payload_client_2)
    resp_login_2 = client.post("/api/v1/auth/login", json={"email": payload_client_2["email"], "password": payload_client_2["password"]})
    token_2 = resp_login_2.json()["access_token"]
    headers_client_2 = {"Authorization": f"Bearer {token_2}"}
    
    resp_book_2 = client.post("/api/v1/appointments", json=booking_payload_1, headers=headers_client_2)
    assert resp_book_2.status_code == 201
    
    # Try booking a third time on the same slot (should fail with 400 because max_slots = 2)
    payload_client_3 = {
        "email": "client3@test.com",
        "password": "strongpassword123",
        "full_name": "Third Client",
        "role": "client",
        "phone": "+54 11 9876 5434"
    }
    register_and_verify(payload_client_3)
    resp_login_3 = client.post("/api/v1/auth/login", json={"email": payload_client_3["email"], "password": payload_client_3["password"]})
    token_3 = resp_login_3.json()["access_token"]
    headers_client_3 = {"Authorization": f"Bearer {token_3}"}
    
    resp_book_3 = client.post("/api/v1/appointments", json=booking_payload_1, headers=headers_client_3)
    assert resp_book_3.status_code == 400
    assert "El horario seleccionado ya está completo" in resp_book_3.json()["detail"]
