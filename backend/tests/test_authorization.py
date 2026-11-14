from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from app.authorization import authorize_patient_read
from app.main import app
from app.models import AuditEvent, CareRelationship, ConsentGrant, Membership, Organization, Patient
from app.security import Principal, get_current_principal

def seed_patient(db, owner_sub="patient-owner", with_org=True):
    organization = Organization(name="Synthetic Clinic") if with_org else None
    if organization:
        db.add(organization)
        db.flush()
    patient = Patient(owner_sub=owner_sub, organization_id=organization.id if organization else None, display_label="Synthetic patient")
    db.add(patient)
    db.commit()
    return patient, organization

def test_patient_can_read_own_profile(client, db_session):
    patient, _ = seed_patient(db_session)
    response = client.get(f"/api/v1/patients/{patient.id}", headers={"X-Correlation-ID": "test-123"})
    assert response.status_code == 200
    assert response.json()["display_label"] == "Synthetic patient"
    event = db_session.query(AuditEvent).one()
    assert (event.outcome, event.correlation_id) == ("allowed", "test-123")

def test_patient_cannot_read_another_patients_profile(client, db_session):
    patient, _ = seed_patient(db_session, owner_sub="someone-else")
    response = client.get(f"/api/v1/patients/{patient.id}")
    assert response.status_code == 404
    assert db_session.query(AuditEvent).one().outcome == "denied"

def seed_clinician_access(db, patient, organization, consent_status="active", expires_at=None):
    clinician = Principal("clinician-1", frozenset({"clinician"}), str(organization.id))
    db.add_all([
        Membership(user_sub=clinician.subject, organization_id=organization.id, role="clinician", status="active"),
        CareRelationship(patient_id=patient.id, clinician_sub=clinician.subject, organization_id=organization.id, status="active"),
        ConsentGrant(patient_id=patient.id, grantee_sub=clinician.subject, scope="patient.read", status=consent_status, expires_at=expires_at, revoked_at=datetime.now(timezone.utc) if consent_status == "revoked" else None),
    ])
    db.commit()
    return clinician

def test_clinician_with_membership_relationship_and_consent_is_allowed(client, db_session):
    patient, org = seed_patient(db_session)
    clinician = seed_clinician_access(db_session, patient, org, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    assert authorize_patient_read(db_session, clinician, patient.id).id == patient.id
    assert db_session.query(AuditEvent).one().outcome == "allowed"

def test_revoked_consent_denies_clinician(client, db_session):
    patient, org = seed_patient(db_session)
    clinician = seed_clinician_access(db_session, patient, org, consent_status="revoked")
    try:
        authorize_patient_read(db_session, clinician, patient.id)
        raise AssertionError("Expected access denial")
    except HTTPException as exc:
        assert exc.status_code == 404
    assert db_session.query(AuditEvent).one().outcome == "denied"

def test_expired_consent_denies_clinician(client, db_session):
    patient, org = seed_patient(db_session)
    clinician = seed_clinician_access(db_session, patient, org, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    try:
        authorize_patient_read(db_session, clinician, patient.id)
        raise AssertionError("Expected access denial")
    except HTTPException as exc:
        assert exc.status_code == 404

def test_membership_without_relationship_or_consent_is_denied(client, db_session):
    patient, org = seed_patient(db_session)
    clinician = Principal("clinician-1", frozenset({"clinician"}), str(org.id))
    db_session.add(Membership(user_sub=clinician.subject, organization_id=org.id, role="clinician"))
    db_session.commit()
    try:
        authorize_patient_read(db_session, clinician, patient.id)
        raise AssertionError("Expected access denial")
    except HTTPException as exc:
        assert exc.status_code == 404

def test_unrecognized_role_is_denied(client, db_session):
    patient, _ = seed_patient(db_session)
    try:
        authorize_patient_read(db_session, Principal("support-1", frozenset({"support"})), patient.id)
        raise AssertionError("Expected access denial")
    except HTTPException as exc:
        assert exc.status_code == 404

def test_missing_bearer_token_is_rejected(client):
    app.dependency_overrides.pop(get_current_principal, None)
    response = client.get("/api/v1/patients/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 401
