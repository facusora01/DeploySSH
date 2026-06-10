import pytest
import uuid
from datetime import datetime
from app.models.service import Service
from app.models.profesional import Profesional
from app.models.weekly_schedule import WeeklySchedule
from app.models.user import User
from app.models.client import Client
from app.models.appointment import Appointment, AppointmentStatus, DepositStatus
from app.models.refund import Refund, RefundStatus


@pytest.fixture
def auth_headers_client_refund(client, register_and_verify):
    payload = {
        "email": "client_refund@test.com",
        "password": "strongpassword123",
        "full_name": "Test Client Refund",
        "role": "client",
        "phone": "+54 11 9876 5432"
    }
    register_and_verify(payload)
    resp = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def setup_deposit_service(db_session, auth_headers_profesional):
    user = db_session.query(User).filter(User.email == "pro@test.com").first()
    assert user is not None

    profesional = db_session.query(Profesional).filter(Profesional.user_id == user.id).first()
    assert profesional is not None

    service = Service(
        profesional_id=profesional.id,
        name="Deposit Service",
        duration_minutes=30,
        price=100.0,
        max_slots=1,
        is_active=True,
        deposit_active=True,
        deposit_amount=500.0,
        deposit_required=True,
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


def test_cancel_with_paid_deposit_creates_refund(client, auth_headers_client_refund, setup_deposit_service, db_session):
    """Cancelar un turno con seña pagada debe crear un Refund con status PENDING."""
    service = setup_deposit_service

    start_time = datetime(2026, 6, 1, 9, 0)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client_refund)
    assert resp_book.status_code == 201
    appt_id = resp_book.json()["id"]
    assert resp_book.json()["deposit_status"] == "PENDING"

    # Pay deposit
    resp_pay = client.patch(f"/api/v1/appointments/{appt_id}/pay-deposit", headers=auth_headers_client_refund)
    assert resp_pay.status_code == 200
    assert resp_pay.json()["deposit_status"] == "PAID"

    # Cancel appointment
    resp_cancel = client.patch(f"/api/v1/appointments/{appt_id}/cancel", headers=auth_headers_client_refund)
    assert resp_cancel.status_code == 200
    assert resp_cancel.json()["status"] == "cancelled"

    # Check that refund was created in DB
    appt = db_session.get(Appointment, uuid.UUID(appt_id))
    assert appt.refund is not None
    assert appt.refund.status == RefundStatus.PENDING
    assert appt.refund.amount == 500.0


def test_cancel_without_paid_deposit_no_refund(client, auth_headers_client_refund, setup_deposit_service, db_session):
    """Cancelar un turno sin seña pagada no debe crear un Refund."""
    service = setup_deposit_service

    start_time = datetime(2026, 6, 1, 9, 30)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client_refund)
    assert resp_book.status_code == 201
    appt_id = resp_book.json()["id"]

    # Cancel without paying deposit
    resp_cancel = client.patch(f"/api/v1/appointments/{appt_id}/cancel", headers=auth_headers_client_refund)
    assert resp_cancel.status_code == 200

    # Check that no refund was created
    appt = db_session.get(Appointment, uuid.UUID(appt_id))
    assert appt.refund is None


def test_get_refunds_as_profesional(client, auth_headers_client_refund, setup_deposit_service):
    """Profesional puede ver sus reembolsos pendientes."""
    service = setup_deposit_service

    start_time = datetime(2026, 6, 2, 9, 0)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client_refund)
    appt_id = resp_book.json()["id"]

    # Pay deposit and cancel
    client.patch(f"/api/v1/appointments/{appt_id}/pay-deposit", headers=auth_headers_client_refund)
    client.patch(f"/api/v1/appointments/{appt_id}/cancel", headers=auth_headers_client_refund)

    # Login as profesional
    resp_pro_login = client.post("/api/v1/auth/login", json={"email": "pro@test.com", "password": "strongpassword123"})
    pro_token = resp_pro_login.json()["access_token"]
    pro_headers = {"Authorization": f"Bearer {pro_token}"}

    # Get refunds
    resp = client.get("/api/v1/refunds", headers=pro_headers)
    assert resp.status_code == 200
    refunds = resp.json()
    assert len(refunds) > 0
    assert refunds[0]["status"] == "PENDING"
    assert refunds[0]["amount"] == 500.0


def test_mark_refund_done_as_profesional(client, auth_headers_client_refund, setup_deposit_service):
    """Profesional puede marcar un reembolso como realizado."""
    service = setup_deposit_service

    start_time = datetime(2026, 6, 3, 9, 0)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client_refund)
    appt_id = resp_book.json()["id"]

    # Pay deposit and cancel
    client.patch(f"/api/v1/appointments/{appt_id}/pay-deposit", headers=auth_headers_client_refund)
    client.patch(f"/api/v1/appointments/{appt_id}/cancel", headers=auth_headers_client_refund)

    # Login as profesional
    resp_pro_login = client.post("/api/v1/auth/login", json={"email": "pro@test.com", "password": "strongpassword123"})
    pro_token = resp_pro_login.json()["access_token"]
    pro_headers = {"Authorization": f"Bearer {pro_token}"}

    # Get refunds
    resp = client.get("/api/v1/refunds", headers=pro_headers)
    refund_id = resp.json()[0]["id"]

    # Mark as done
    resp_mark = client.patch(f"/api/v1/refunds/{refund_id}/mark-done", headers=pro_headers)
    assert resp_mark.status_code == 200
    assert resp_mark.json()["status"] == "DONE"


def test_mark_refund_done_as_client_forbidden(client, auth_headers_client_refund, setup_deposit_service):
    """Cliente no puede marcar un reembolso como realizado."""
    service = setup_deposit_service

    start_time = datetime(2026, 6, 4, 9, 0)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client_refund)
    appt_id = resp_book.json()["id"]

    # Pay deposit and cancel
    client.patch(f"/api/v1/appointments/{appt_id}/pay-deposit", headers=auth_headers_client_refund)
    client.patch(f"/api/v1/appointments/{appt_id}/cancel", headers=auth_headers_client_refund)

    # Login as profesional to get refund_id
    resp_pro_login = client.post("/api/v1/auth/login", json={"email": "pro@test.com", "password": "strongpassword123"})
    pro_token = resp_pro_login.json()["access_token"]
    pro_headers = {"Authorization": f"Bearer {pro_token}"}

    resp = client.get("/api/v1/refunds", headers=pro_headers)
    refund_id = resp.json()[0]["id"]

    # Try to mark as done as client
    resp_mark = client.patch(f"/api/v1/refunds/{refund_id}/mark-done", headers=auth_headers_client_refund)
    assert resp_mark.status_code == 403
    assert "No tenés permiso" in resp_mark.json()["detail"]


def test_mark_refund_done_when_not_pending(client, auth_headers_client_refund, setup_deposit_service):
    """No se puede marcar un reembolso como realizado si no está pendiente."""
    service = setup_deposit_service

    start_time = datetime(2026, 6, 5, 9, 0)
    booking_payload = {
        "service_id": str(service.id),
        "start_time": start_time.isoformat()
    }
    resp_book = client.post("/api/v1/appointments", json=booking_payload, headers=auth_headers_client_refund)
    appt_id = resp_book.json()["id"]

    # Pay deposit and cancel
    client.patch(f"/api/v1/appointments/{appt_id}/pay-deposit", headers=auth_headers_client_refund)
    client.patch(f"/api/v1/appointments/{appt_id}/cancel", headers=auth_headers_client_refund)

    # Login as profesional
    resp_pro_login = client.post("/api/v1/auth/login", json={"email": "pro@test.com", "password": "strongpassword123"})
    pro_token = resp_pro_login.json()["access_token"]
    pro_headers = {"Authorization": f"Bearer {pro_token}"}

    # Get refunds and mark as done
    resp = client.get("/api/v1/refunds", headers=pro_headers)
    refund_id = resp.json()[0]["id"]

    client.patch(f"/api/v1/refunds/{refund_id}/mark-done", headers=pro_headers)

    # Try to mark as done again
    resp_mark = client.patch(f"/api/v1/refunds/{refund_id}/mark-done", headers=pro_headers)
    assert resp_mark.status_code == 400
    assert "no está pendiente" in resp_mark.json()["detail"]


def test_get_refunds_filtered_by_status(client, auth_headers_client_refund, setup_deposit_service):
    """Profesional puede filtrar reembolsos por status."""
    service = setup_deposit_service

    # Create and cancel first appointment
    start_time1 = datetime(2026, 6, 6, 9, 0)
    booking_payload1 = {
        "service_id": str(service.id),
        "start_time": start_time1.isoformat()
    }
    resp_book1 = client.post("/api/v1/appointments", json=booking_payload1, headers=auth_headers_client_refund)
    appt_id1 = resp_book1.json()["id"]
    client.patch(f"/api/v1/appointments/{appt_id1}/pay-deposit", headers=auth_headers_client_refund)
    client.patch(f"/api/v1/appointments/{appt_id1}/cancel", headers=auth_headers_client_refund)

    # Login as profesional
    resp_pro_login = client.post("/api/v1/auth/login", json={"email": "pro@test.com", "password": "strongpassword123"})
    pro_token = resp_pro_login.json()["access_token"]
    pro_headers = {"Authorization": f"Bearer {pro_token}"}

    # Get pending refunds
    resp = client.get("/api/v1/refunds?status_filter=PENDING", headers=pro_headers)
    assert resp.status_code == 200
    pending = resp.json()
    assert len(pending) == 1
    assert pending[0]["status"] == "PENDING"

    # Mark as done
    client.patch(f"/api/v1/refunds/{pending[0]['id']}/mark-done", headers=pro_headers)

    # Get done refunds
    resp = client.get("/api/v1/refunds?status_filter=DONE", headers=pro_headers)
    assert resp.status_code == 200
    done = resp.json()
    assert len(done) == 1
    assert done[0]["status"] == "DONE"
