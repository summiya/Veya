from fastapi.testclient import TestClient

from veya.infrastructure.health.service import DependencyHealth
from veya.main import app


client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Veya",
        "status": "running",
        "version": "0.1.0",
    }


def test_health_liveness() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Veya",
        "version": "0.1.0",
    }


def test_legacy_health_path_remains_available() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_readiness_reports_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(
        "veya.api.routes.health.HealthService.check",
        lambda self: DependencyHealth(
            status="ok",
            database="ok",
            redis="ok",
        ),
    )

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["dependencies"] == {
        "database": "ok",
        "redis": "ok",
    }


def test_readiness_returns_503_when_dependency_is_down(monkeypatch) -> None:
    alerts: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        "veya.api.routes.health.capture_operational_alert",
        lambda message, **kwargs: alerts.append((message, kwargs)) or True,
    )
    monkeypatch.setattr(
        "veya.api.routes.health.HealthService.check",
        lambda self: DependencyHealth(
            status="degraded",
            database="ok",
            redis="unavailable",
        ),
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["dependencies"]["redis"] == "unavailable"
    assert alerts[0][0] == "Veya readiness degraded"
    assert alerts[0][1]["event"] == "readiness_degraded"
    assert alerts[0][1]["tags"]["redis"] == "unavailable"


def test_request_id_is_returned_and_preserved() -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "test-request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-123"


def test_request_id_is_generated_when_missing() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_openapi_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Veya API"
