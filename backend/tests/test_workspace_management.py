from uuid import uuid4
from app.main import app
from app.models import Organization, Patient, WorkspaceEntry, WorkspaceMenuItem, Membership
from app.security import Principal, get_current_principal


def test_patient_can_create_list_update_and_archive_appointment_request(client, db_session):
    bootstrap = client.post("/api/v1/workspace/bootstrap")
    patient_id = bootstrap.json()["patient_id"]
    created = client.post("/api/v1/workspace/entries", json={
        "resource_type": "appointment_request", "patient_id": patient_id,
        "data": {"reason": "Annual review", "preferred_date": "2026-12-02"},
    })
    assert created.status_code == 201
    entry_id = created.json()["id"]
    assert client.get("/api/v1/workspace/entries?resource_type=appointment_request").json()[0]["id"] == entry_id
    updated = client.patch(f"/api/v1/workspace/entries/{entry_id}", json={
        "data": {"reason": "Annual review", "preferred_date": "2026-12-03"}
    })
    assert updated.status_code == 200
    assert updated.json()["data"]["preferred_date"] == "2026-12-03"
    archived = client.delete(f"/api/v1/workspace/entries/{entry_id}")
    assert archived.status_code == 204
    assert client.get("/api/v1/workspace/entries?resource_type=appointment_request").json() == []


def test_patient_cannot_create_clinical_note(client):
    response = client.post("/api/v1/workspace/entries", json={
        "resource_type": "clinical_note", "data": {"title": "Not allowed"}
    })
    assert response.status_code == 403


def test_patient_cannot_access_another_patients_entry(client, db_session):
    own = client.post("/api/v1/workspace/bootstrap").json()["patient_id"]
    other = Patient(owner_sub="someone-else", display_label="Other patient")
    db_session.add(other)
    db_session.flush()
    row = WorkspaceEntry(resource_type="appointment_request", patient_id=other.id,
        owner_sub="someone-else", data={"reason": "Private"}, created_by="someone-else",
        updated_by="someone-else")
    db_session.add(row)
    db_session.commit()
    response = client.get(f"/api/v1/workspace/entries?resource_type=appointment_request&patient_id={other.id}")
    assert response.status_code == 404


def test_admin_can_create_update_and_archive_role_menu(client, db_session):
    app.dependency_overrides[get_current_principal] = lambda: Principal("admin-1", frozenset({"admin"}))
    created = client.post("/api/v1/workspace/menus", json={
        "key": "clinic-analytics", "label": "Clinic analytics", "path": "/portal/analytics",
        "icon": "chart-no-axes-combined", "roles": ["admin"], "sort_order": 20
    })
    assert created.status_code == 201
    menu_id = created.json()["id"]
    assert client.get("/api/v1/workspace/menus").json()[0]["key"] == "clinic-analytics"
    updated = client.patch(f"/api/v1/workspace/menus/{menu_id}", json={"label": "Analytics"})
    assert updated.status_code == 200
    assert updated.json()["label"] == "Analytics"
    assert client.delete(f"/api/v1/workspace/menus/{menu_id}").status_code == 204
    assert client.get("/api/v1/workspace/menus").json() == []


def test_non_admin_cannot_manage_menus(client):
    response = client.post("/api/v1/workspace/menus", json={
        "key": "hidden-menu", "label": "Hidden", "path": "/hidden",
        "roles": ["patient"]
    })
    assert response.status_code == 403


def test_receptionist_requires_active_membership_for_appointments(client, db_session):
    org = Organization(name="Clinic")
    db_session.add(org)
    db_session.flush()
    patient = Patient(owner_sub="patient-1", organization_id=org.id, display_label="Demo patient")
    db_session.add(patient)
    db_session.commit()
    app.dependency_overrides[get_current_principal] = lambda: Principal("frontdesk-1", frozenset({"receptionist"}))
    denied = client.post("/api/v1/workspace/entries", json={
        "resource_type": "appointment", "patient_id": str(patient.id),
        "data": {"scheduled_at": "2026-12-01T09:00:00Z"}
    })
    assert denied.status_code == 403
    db_session.add(Membership(user_sub="frontdesk-1", organization_id=org.id,
        role="receptionist", status="active"))
    db_session.commit()
    allowed = client.post("/api/v1/workspace/entries", json={
        "resource_type": "appointment", "patient_id": str(patient.id),
        "data": {"scheduled_at": "2026-12-01T09:00:00Z"}
    })
    assert allowed.status_code == 201
