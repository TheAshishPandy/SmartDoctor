from datetime import datetime, timezone
from uuid import UUID, uuid4
from app.models import AuthUser, CareRelationship, ConsentGrant, Membership, Organization, Patient, WorkspaceEntry
from app.security import Principal, get_current_principal


def principal(subject, *roles):
    return Principal(subject, frozenset(roles))


def test_super_admin_can_create_and_list_organizations(client, db_session):
    db_session.add(AuthUser(id=uuid4(), email="platform@example.test", password_hash="x",
        display_name="Platform", role="super_admin", is_verified=True))
    db_session.commit()
    app = client.app
    app.dependency_overrides[get_current_principal] = lambda: principal("platform", "super_admin")
    created = client.post("/api/v1/super-admin/organizations",
        json={"name": "North Clinic", "chatbot_enabled": True})
    assert created.status_code == 201
    assert created.json()["chatbot"]["enabled"] is True
    listed = client.get("/api/v1/super-admin/organizations")
    assert listed.status_code == 200
    assert any(row["name"] == "North Clinic" for row in listed.json())


def test_organization_admin_cannot_use_platform_super_admin_api(client, db_session):
    app = client.app
    app.dependency_overrides[get_current_principal] = lambda: principal("clinic-admin", "admin")
    response = client.get("/api/v1/super-admin/organizations")
    assert response.status_code == 403


def test_clinic_chat_finds_doctor_by_specialty_and_requests_slot(client, db_session):
    organization = Organization(name="Cardio Clinic", status="active", chatbot_config={"enabled": True})
    doctor = AuthUser(email="doctor@example.test", password_hash="x", display_name="Dr Cardio",
        role="doctor", is_verified=True)
    patient_user = AuthUser(email="patient@example.test", password_hash="x", display_name="Patient",
        role="patient", is_verified=True)
    db_session.add_all([organization, doctor, patient_user])
    db_session.flush()
    patient = Patient(owner_sub=str(patient_user.id), organization_id=organization.id, display_label="Patient")
    membership = Membership(user_sub=str(doctor.id), organization_id=organization.id, role="clinician",
        status="active", specialties=["Cardiology"], availability={"slots": ["2026-11-23T10:00:00+05:30"]})
    db_session.add_all([patient, membership])
    db_session.commit()
    app = client.app
    app.dependency_overrides[get_current_principal] = lambda: principal(str(patient_user.id), "patient")
    response = client.post("/api/v1/clinic/chat", json={
        "intent": "book_appointment", "message": "Please book a heart consultation",
        "specialty": "Cardiology", "preferred_at": "2026-11-23T04:30:00Z",
        "reason": "Heart check-up"
    })
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["booked"] is True
    entry = db_session.get(WorkspaceEntry, UUID(body["appointment_id"]))
    assert entry is not None
    assert entry.resource_type == "appointment"
    assert entry.data["doctor_id"] == str(doctor.id)
    assert db_session.get(Membership, membership.id).availability["slots"] == []
    duplicate = client.post("/api/v1/clinic/chat", json={
        "intent": "book_appointment", "message": "Book the same slot again", "specialty": "Cardiology",
        "preferred_at": "2026-11-23T04:30:00Z"
    })
    assert duplicate.status_code == 200
    assert duplicate.json()["booked"] is False


def test_patient_can_grant_and_revoke_doctor_consent(client, db_session):
    organization = Organization(name="Care Clinic", status="active")
    doctor = AuthUser(email="clinician@example.test", password_hash="x", display_name="Dr Care",
        role="doctor", is_verified=True)
    patient_user = AuthUser(email="owner@example.test", password_hash="x", display_name="Patient",
        role="patient", is_verified=True)
    db_session.add_all([organization, doctor, patient_user])
    db_session.flush()
    patient = Patient(owner_sub=str(patient_user.id), organization_id=organization.id, display_label="Patient")
    db_session.add_all([patient, Membership(user_sub=str(doctor.id), organization_id=organization.id,
        role="clinician", status="active", specialties=["General Medicine"])])
    db_session.commit()
    client.app.dependency_overrides[get_current_principal] = lambda: principal(str(patient_user.id), "patient")
    payload = {"organization_id": str(organization.id), "doctor_user_id": str(doctor.id), "consent": True}
    granted = client.post("/api/v1/clinic/consent", json=payload)
    assert granted.status_code == 200
    assert db_session.query(CareRelationship).filter_by(patient_id=patient.id, status="active").count() == 1
    payload["consent"] = False
    revoked = client.post("/api/v1/clinic/consent", json=payload)
    assert revoked.status_code == 200
    assert revoked.json()["consent"] == "revoked"
    assert db_session.query(ConsentGrant).filter_by(patient_id=patient.id, status="revoked").count() == 1

def test_super_admin_role_is_bootstrapped_from_trusted_email_allowlist(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("AUTH_SUPER_ADMIN_EMAILS", "platform-owner@example.com")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AUTH_DEV_OTP_ENABLED", "true")
    monkeypatch.setenv("SMTP_HOST", "")
    get_settings.cache_clear()
    try:
        registered = client.post("/api/v1/auth/register", json={
            "email": "platform-owner@example.com",
            "password": "a-strong-platform-password",
            "display_name": "Platform Owner",
        })
        assert registered.status_code == 202
        otp = registered.json()["development_otp"]
        verified = client.post("/api/v1/auth/verify-email", json={
            "email": "platform-owner@example.com", "code": otp,
        })
        assert verified.status_code == 200
        login = client.post("/api/v1/auth/login", json={
            "email": "platform-owner@example.com",
            "password": "a-strong-platform-password",
        })
        assert login.status_code == 200
        assert login.json()["user"]["role"] == "super_admin"
    finally:
        get_settings.cache_clear()
