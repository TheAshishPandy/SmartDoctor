import pytest
from app.config import get_settings
from app.main import app
from app.security import get_current_principal


@pytest.fixture(autouse=True)
def auth_test_settings(monkeypatch):
    monkeypatch.setenv("AUTH_JWT_SECRET", "unit-test-signing-secret-at-least-32-characters")
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AUTH_DEV_OTP_ENABLED", "true")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_register_verify_login_and_me(client):
    registered = client.post("/api/v1/auth/register", json={
        "email": "patient@example.com",
        "password": "a-strong-password-123",
        "display_name": "Test Patient",
    })
    assert registered.status_code == 202
    otp = registered.json()["development_otp"]

    verified = client.post("/api/v1/auth/verify-email", json={
        "email": "patient@example.com", "code": otp,
    })
    assert verified.status_code == 200

    login = client.post("/api/v1/auth/login", json={
        "email": "patient@example.com", "password": "a-strong-password-123",
    })
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "patient"
    assert "smartdoctor_refresh=" in login.headers.get("set-cookie", "")

    app.dependency_overrides.pop(get_current_principal, None)
    me = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {login.json()['access_token']}",
    })
    assert me.status_code == 200
    assert me.json()["email"] == "patient@example.com"

    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != login.json()["access_token"]
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_unverified_user_cannot_login(client):
    client.post("/api/v1/auth/register", json={
        "email": "pending@example.com",
        "password": "a-strong-password-123",
        "display_name": "Pending User",
    })
    response = client.post("/api/v1/auth/login", json={
        "email": "pending@example.com", "password": "a-strong-password-123",
    })
    assert response.status_code == 403


def test_public_registration_cannot_choose_privileged_role(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "doctor@example.com",
        "password": "a-strong-password-123",
        "display_name": "Doctor User",
        "role": "doctor",
    })
    assert response.status_code == 202
    otp = response.json()["development_otp"]
    client.post("/api/v1/auth/verify-email", json={"email": "doctor@example.com", "code": otp})
    login = client.post("/api/v1/auth/login", json={
        "email": "doctor@example.com", "password": "a-strong-password-123",
    })
    assert login.json()["user"]["role"] == "patient"


def test_wrong_otp_is_rejected(client):
    client.post("/api/v1/auth/register", json={
        "email": "wrongotp@example.com",
        "password": "a-strong-password-123",
        "display_name": "Wrong OTP",
    })
    response = client.post("/api/v1/auth/verify-email", json={
        "email": "wrongotp@example.com", "code": "999999",
    })
    assert response.status_code == 400


def test_smtp_delivery_response_never_contains_otp(client, monkeypatch):
    import app.api.auth as auth_api

    async def email_sent(_email, _code, _purpose):
        return False

    monkeypatch.setattr(auth_api, "_send_otp", email_sent)
    response = client.post("/api/v1/auth/register", json={
        "email": "smtp-user@example.com",
        "password": "a-strong-password-123",
        "display_name": "SMTP User",
    })
    assert response.status_code == 202
    assert "development_otp" not in response.json()
