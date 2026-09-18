from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError

from veya.api.middleware.rate_limit import RateLimitMiddleware
from veya.core.config import settings


class FakeRedis:
    def __init__(self, counts: list[int] | None = None, error: Exception | None = None):
        self.counts = counts or []
        self.error = error

    def eval(self, *args):
        if self.error is not None:
            raise self.error
        return self.counts.pop(0)


def make_app(fake_redis: FakeRedis) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, redis_client=fake_redis)

    @app.post("/api/auth/login")
    async def login():
        return {"ok": True}

    return app


def test_rate_limit_allows_request_and_sets_headers() -> None:
    original_enabled = settings.rate_limit_enabled
    original_limit = settings.rate_limit_login_per_minute
    try:
        settings.rate_limit_enabled = True
        settings.rate_limit_login_per_minute = 2
        response = TestClient(make_app(FakeRedis([1]))).post("/api/auth/login")
    finally:
        settings.rate_limit_enabled = original_enabled
        settings.rate_limit_login_per_minute = original_limit

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "1"


def test_rate_limit_returns_429_after_limit() -> None:
    original_enabled = settings.rate_limit_enabled
    original_limit = settings.rate_limit_login_per_minute
    try:
        settings.rate_limit_enabled = True
        settings.rate_limit_login_per_minute = 1
        response = TestClient(make_app(FakeRedis([2]))).post("/api/auth/login")
    finally:
        settings.rate_limit_enabled = original_enabled
        settings.rate_limit_login_per_minute = original_limit

    assert response.status_code == 429
    assert response.json()["detail"].startswith("Too many requests")
    assert int(response.headers["Retry-After"]) >= 1


def test_rate_limit_fails_open_when_redis_is_unavailable() -> None:
    original_enabled = settings.rate_limit_enabled
    original_fail_open = settings.rate_limit_fail_open
    try:
        settings.rate_limit_enabled = True
        settings.rate_limit_fail_open = True
        response = TestClient(
            make_app(FakeRedis(error=RedisConnectionError("redis unavailable")))
        ).post("/api/auth/login")
    finally:
        settings.rate_limit_enabled = original_enabled
        settings.rate_limit_fail_open = original_fail_open

    assert response.status_code == 200


def test_rate_limit_can_fail_closed_when_configured() -> None:
    original_enabled = settings.rate_limit_enabled
    original_fail_open = settings.rate_limit_fail_open
    try:
        settings.rate_limit_enabled = True
        settings.rate_limit_fail_open = False
        response = TestClient(
            make_app(FakeRedis(error=RedisConnectionError("redis unavailable")))
        ).post("/api/auth/login")
    finally:
        settings.rate_limit_enabled = original_enabled
        settings.rate_limit_fail_open = original_fail_open

    assert response.status_code == 503


def test_trusted_proxy_ip_is_hashed_not_stored_raw() -> None:
    original_trust = settings.trust_proxy_headers
    try:
        settings.trust_proxy_headers = True
        request = SimpleNamespace(
            headers={"x-forwarded-for": "203.0.113.7"},
            client=SimpleNamespace(host="127.0.0.1"),
        )
        identifier = RateLimitMiddleware._identifier_for_request(request)
    finally:
        settings.trust_proxy_headers = original_trust

    assert identifier != "203.0.113.7"
    assert len(identifier) == 32
