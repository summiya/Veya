from fastapi import FastAPI
from fastapi.testclient import TestClient

from veya.api.middleware.request_context import RequestContextMiddleware


def test_unhandled_error_returns_request_id() -> None:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("boom")

    response = TestClient(app).get(
        "/boom",
        headers={"X-Request-ID": "error-request-123"},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert response.headers["X-Request-ID"] == "error-request-123"


def test_invalid_request_id_is_replaced() -> None:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/ok")
    async def ok():
        return {"ok": True}

    response = TestClient(app).get(
        "/ok",
        headers={"X-Request-ID": "invalid request id with spaces"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "invalid request id with spaces"
    assert response.headers["X-Request-ID"]
