from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import encode_refresh_token
from app.models.local import Local
from app.models.local_invitation import LocalInvitation
from app.models.profesional import Profesional
from app.models.user import User


LOCAL_PAYLOAD = {
    "email": "local@test.com",
    "password": "strongpassword123",
    "full_name": "Dueño del Local",
    "role": "local",
    "phone": "+54 11 9999 0000",
    "local_name": "Salón Beauty",
}


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


def _make_invitation(db_session, local_id, email, raw_token, hours=48):
    invitation = LocalInvitation(
        local_id=local_id,
        email=email,
        token_hash=encode_refresh_token(raw_token),
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=hours),
    )
    db_session.add(invitation)
    db_session.commit()
    db_session.refresh(invitation)
    return invitation


# ── Invite / list / resend / cancel ───────────────────────────────────────────


def test_invite_creates_pending_invitation(client, auth_headers_local):
    resp = client.post(
        "/api/v1/locales/me/invitations",
        json={"email": "Nuevo.Pro@test.com"},
        headers=auth_headers_local,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "nuevo.pro@test.com"  # normalized to lowercase
    assert body["status"] == "pending"

    listed = client.get(
        "/api/v1/locales/me/invitations", headers=auth_headers_local
    ).json()
    assert len(listed) == 1
    assert listed[0]["email"] == "nuevo.pro@test.com"


def test_invite_twice_same_email_updates_not_duplicates(client, auth_headers_local):
    client.post(
        "/api/v1/locales/me/invitations",
        json={"email": "dup@test.com"},
        headers=auth_headers_local,
    )
    client.post(
        "/api/v1/locales/me/invitations",
        json={"email": "dup@test.com"},
        headers=auth_headers_local,
    )
    listed = client.get(
        "/api/v1/locales/me/invitations", headers=auth_headers_local
    ).json()
    assert len(listed) == 1


def test_resend_invitation_extends_expiry(client, auth_headers_local, db_session, local_profile):
    inv = _make_invitation(db_session, local_profile.id, "resend@test.com", "tok-resend", hours=1)
    old_expiry = inv.expires_at

    resp = client.post(
        f"/api/v1/locales/me/invitations/{inv.id}/resend",
        headers=auth_headers_local,
    )
    assert resp.status_code == 200

    db_session.refresh(inv)
    assert inv.expires_at > old_expiry


def test_cancel_invitation_removes_it(client, auth_headers_local, db_session, local_profile):
    inv = _make_invitation(db_session, local_profile.id, "cancel@test.com", "tok-cancel")

    resp = client.delete(
        f"/api/v1/locales/me/invitations/{inv.id}", headers=auth_headers_local
    )
    assert resp.status_code == 204

    listed = client.get(
        "/api/v1/locales/me/invitations", headers=auth_headers_local
    ).json()
    assert listed == []


def test_non_local_cannot_invite(client, auth_headers_profesional):
    resp = client.post(
        "/api/v1/locales/me/invitations",
        json={"email": "x@test.com"},
        headers=auth_headers_profesional,
    )
    assert resp.status_code == 403


def test_invite_email_of_non_profesional_account_is_rejected(
    client, auth_headers_local, register_and_verify
):
    # El email pertenece a una cuenta de cliente -> no se puede invitar
    register_and_verify(
        {
            "email": "cliente@test.com",
            "password": "strongpassword123",
            "full_name": "Un Cliente",
            "role": "client",
            "phone": "+54 11 0000 1111",
        }
    )
    resp = client.post(
        "/api/v1/locales/me/invitations",
        json={"email": "cliente@test.com"},
        headers=auth_headers_local,
    )
    assert resp.status_code == 409

    # No debe haberse creado ninguna invitación
    listed = client.get(
        "/api/v1/locales/me/invitations", headers=auth_headers_local
    ).json()
    assert listed == []


# ── Invitation info (public) ───────────────────────────────────────────────────


def test_invitation_info_for_unknown_email(client, db_session, local_profile):
    _make_invitation(db_session, local_profile.id, "ghost@test.com", "tok-info")

    resp = client.get("/api/v1/locales/invitations/tok-info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["local_name"] == "Salón Beauty"
    assert body["email"] == "ghost@test.com"
    assert body["account_exists"] is False
    assert body["account_is_profesional"] is False
    assert body["expired"] is False


def test_invitation_info_not_found(client):
    resp = client.get("/api/v1/locales/invitations/does-not-exist")
    assert resp.status_code == 404


# ── Accept (existing professional account) ─────────────────────────────────────


def test_existing_profesional_accepts_and_gets_linked(
    client, auth_headers_local, auth_headers_profesional, db_session, local_profile
):
    _make_invitation(db_session, local_profile.id, "pro@test.com", "tok-accept")

    resp = client.post(
        "/api/v1/locales/invitations/tok-accept/accept",
        headers=auth_headers_profesional,
    )
    assert resp.status_code == 200

    prof = db_session.query(Profesional).join(User).filter(User.email == "pro@test.com").first()
    db_session.refresh(prof)
    assert prof.local_id == local_profile.id


def test_accept_with_mismatched_email_is_forbidden(
    client, auth_headers_local, auth_headers_profesional, db_session, local_profile
):
    # invitation addressed to a different email than the logged-in professional
    _make_invitation(db_session, local_profile.id, "someoneelse@test.com", "tok-mismatch")

    resp = client.post(
        "/api/v1/locales/invitations/tok-mismatch/accept",
        headers=auth_headers_profesional,
    )
    assert resp.status_code == 403


def test_accept_expired_invitation_fails(
    client, auth_headers_local, auth_headers_profesional, db_session, local_profile
):
    _make_invitation(db_session, local_profile.id, "pro@test.com", "tok-expired", hours=-1)

    resp = client.post(
        "/api/v1/locales/invitations/tok-expired/accept",
        headers=auth_headers_profesional,
    )
    assert resp.status_code == 400


# ── Accept via registration (new account) ──────────────────────────────────────


def test_register_with_invitation_token_links_professional(
    client, auth_headers_local, db_session, local_profile, register_and_verify
):
    _make_invitation(db_session, local_profile.id, "brandnew@test.com", "tok-register")

    register_and_verify(
        {
            "email": "brandnew@test.com",
            "password": "strongpassword123",
            "full_name": "Brand New Pro",
            "role": "profesional",
            "phone": "+54 11 1111 2222",
            "specialty": "Estética",
            "invitation_token": "tok-register",
        }
    )

    prof = (
        db_session.query(Profesional)
        .join(User)
        .filter(User.email == "brandnew@test.com")
        .first()
    )
    assert prof is not None
    assert prof.local_id == local_profile.id

    db_session.refresh(prof)
    inv = (
        db_session.query(LocalInvitation)
        .filter(LocalInvitation.email == "brandnew@test.com")
        .first()
    )
    assert inv.status == "accepted"


# ── In-app notification + received invitations ─────────────────────────────────


def test_invite_existing_profesional_creates_inapp_notification(
    client, auth_headers_local, auth_headers_profesional
):
    client.post(
        "/api/v1/locales/me/invitations",
        json={"email": "pro@test.com"},
        headers=auth_headers_local,
    )
    notifs = client.get("/api/v1/notifications", headers=auth_headers_profesional).json()
    assert any(n["type"] == "TEAM_INVITATION" for n in notifs)


def test_received_invitation_listed_and_accepted(
    client, auth_headers_local, auth_headers_profesional, db_session, local_profile
):
    _make_invitation(db_session, local_profile.id, "pro@test.com", "tok-recv")

    received = client.get(
        "/api/v1/locales/invitations/received", headers=auth_headers_profesional
    ).json()
    assert len(received) == 1
    assert received[0]["local_name"] == "Salón Beauty"

    resp = client.post(
        f"/api/v1/locales/invitations/received/{received[0]['id']}/accept",
        headers=auth_headers_profesional,
    )
    assert resp.status_code == 200

    prof = db_session.query(Profesional).join(User).filter(User.email == "pro@test.com").first()
    db_session.refresh(prof)
    assert prof.local_id == local_profile.id


def test_accept_received_addressed_to_other_email_is_forbidden(
    client, auth_headers_local, auth_headers_profesional, db_session, local_profile
):
    inv = _make_invitation(db_session, local_profile.id, "otro@test.com", "tok-recv-other")

    resp = client.post(
        f"/api/v1/locales/invitations/received/{inv.id}/accept",
        headers=auth_headers_profesional,
    )
    assert resp.status_code == 403


# ── Reject ─────────────────────────────────────────────────────────────────────


def test_reject_received_invitation(
    client, auth_headers_local, auth_headers_profesional, db_session, local_profile
):
    inv = _make_invitation(db_session, local_profile.id, "pro@test.com", "tok-reject")

    resp = client.post(
        f"/api/v1/locales/invitations/received/{inv.id}/reject",
        headers=auth_headers_profesional,
    )
    assert resp.status_code == 200

    db_session.refresh(inv)
    assert inv.status == "rejected"

    # ya no aparece en recibidas
    received = client.get(
        "/api/v1/locales/invitations/received", headers=auth_headers_profesional
    ).json()
    assert received == []

    # el profesional NO quedó vinculado
    prof = db_session.query(Profesional).join(User).filter(User.email == "pro@test.com").first()
    db_session.refresh(prof)
    assert prof.local_id is None


def test_reject_invitation_by_token(
    client, auth_headers_local, auth_headers_profesional, db_session, local_profile
):
    inv = _make_invitation(db_session, local_profile.id, "pro@test.com", "tok-reject-2")

    resp = client.post(
        "/api/v1/locales/invitations/tok-reject-2/reject",
        headers=auth_headers_profesional,
    )
    assert resp.status_code == 200

    db_session.refresh(inv)
    assert inv.status == "rejected"


def test_reject_after_accept_is_conflict(
    client, auth_headers_local, auth_headers_profesional, db_session, local_profile
):
    inv = _make_invitation(db_session, local_profile.id, "pro@test.com", "tok-acc-rej")

    client.post(
        f"/api/v1/locales/invitations/received/{inv.id}/accept",
        headers=auth_headers_profesional,
    )
    resp = client.post(
        f"/api/v1/locales/invitations/received/{inv.id}/reject",
        headers=auth_headers_profesional,
    )
    assert resp.status_code == 409
