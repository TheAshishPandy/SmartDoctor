from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "smartdoctor-api",
        "version": app.version,
    }


def test_openapi_is_available_outside_production() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "SmartDoctor API"
