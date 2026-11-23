from uuid import uuid4

from app.models import Membership, Organization, Patient
from app.security import get_current_principal


def principal(subject, *roles):
    from app.security import Principal
    return Principal(subject, frozenset(roles))


def test_super_admin_can_publish_global_theme(client):
    client.app.dependency_overrides[get_current_principal] = lambda: principal("platform", "super_admin")
    response = client.patch("/api/v1/super-admin/theme", json={"preset": "ocean-blue"})
    assert response.status_code == 200
    assert response.json()["preset"] == "ocean-blue"
    assert client.get("/api/v1/super-admin/theme").json()["preset"] == "ocean-blue"


def test_super_admin_can_assign_and_clear_organization_theme(client, db_session):
    organization = Organization(name="Theme Clinic", status="active")
    db_session.add(organization)
    db_session.commit()
    client.app.dependency_overrides[get_current_principal] = lambda: principal("platform", "super_admin")

    assigned = client.patch(f"/api/v1/super-admin/organizations/{organization.id}/theme",
        json={"preset": "sage-wellness"})
    assert assigned.status_code == 200
    assert assigned.json()["effective_preset"] == "sage-wellness"

    cleared = client.patch(f"/api/v1/super-admin/organizations/{organization.id}/theme",
        json={"preset": "inherit"})
    assert cleared.status_code == 200
    assert cleared.json()["preset"] == "inherit"
    assert db_session.get(Organization, organization.id).ui_theme == {}


def test_active_theme_resolves_organization_override(client, db_session):
    organization = Organization(name="Sage Clinic", status="active", ui_theme={"preset": "sage-wellness"})
    db_session.add(organization)
    db_session.flush()
    membership = Membership(user_sub="doctor-user", organization_id=organization.id,
        role="clinician", status="active")
    db_session.add(membership)
    db_session.commit()
    client.app.dependency_overrides[get_current_principal] = lambda: principal("doctor-user", "doctor", "clinician")

    response = client.get("/api/v1/themes/active")
    assert response.status_code == 200
    assert response.json()["preset"] == "sage-wellness"
    assert response.json()["source"] == "organization"
    assert response.json()["organization_id"] == str(organization.id)


def test_organization_admin_cannot_change_platform_or_tenant_theme(client, db_session):
    organization = Organization(name="Restricted Clinic", status="active")
    db_session.add(organization)
    db_session.commit()
    client.app.dependency_overrides[get_current_principal] = lambda: principal("clinic-admin", "admin")

    global_response = client.patch("/api/v1/super-admin/theme", json={"preset": "warm-sand"})
    tenant_response = client.patch(f"/api/v1/super-admin/organizations/{organization.id}/theme",
        json={"preset": "warm-sand"})
    assert global_response.status_code == 403
    assert tenant_response.status_code == 403


def test_unknown_theme_preset_is_rejected(client):
    client.app.dependency_overrides[get_current_principal] = lambda: principal("platform", "super_admin")
    response = client.patch("/api/v1/super-admin/theme", json={"preset": "custom-css"})
    assert response.status_code == 422
