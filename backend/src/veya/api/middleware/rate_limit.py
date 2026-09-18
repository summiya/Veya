import hashlib
import logging
import time
from dataclasses import dataclass

from redis import Redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from veya.core.config import settings


logger = logging.getLogger("veya.security")


@dataclass(frozen=True)
class RateLimitRule:
    method: str
    path: str
    limit: int
    window_seconds: int
    name: str


INCREMENT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client or Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )

    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled:
            return await call_next(request)

        rule = self._match_rule(request)
        if rule is None:
            return await call_next(request)

        identifier = self._identifier_for_request(request)
        now = int(time.time())
        window = now // rule.window_seconds
        redis_key = f"rate-limit:{rule.name}:{identifier}:{window}"
        reset_at = (window + 1) * rule.window_seconds
        retry_after = max(1, reset_at - now)

        try:
            count = int(
                self.redis.eval(
                    INCREMENT_SCRIPT,
                    1,
                    redis_key,
                    rule.window_seconds + 1,
                )
            )
        except RedisError as exc:
            logger.warning(
                "Rate limiter unavailable",
                extra={
                    "event": "rate_limit_unavailable",
                    "path": request.url.path,
                    "error_type": type(exc).__name__,
                },
            )
            if settings.rate_limit_fail_open:
                return await call_next(request)

            return JSONResponse(
                status_code=503,
                content={"detail": "Request protection is temporarily unavailable"},
                headers={"Retry-After": "1"},
            )

        remaining = max(0, rule.limit - count)

        if count > rule.limit:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "event": "rate_limit_exceeded",
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rule.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rule.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response

    @staticmethod
    def _identifier_for_request(request: Request) -> str:
        client_ip = RateLimitMiddleware._client_ip(request)
        return hashlib.sha256(client_ip.encode()).hexdigest()[:32]

    @staticmethod
    def _client_ip(request: Request) -> str:
        if settings.trust_proxy_headers:
            forwarded = request.headers.get("x-forwarded-for", "").strip()
            if forwarded:
                return forwarded.split(",")[0].strip()

        if request.client is not None and request.client.host:
            return request.client.host

        return "unknown"

    @staticmethod
    def _match_rule(request: Request) -> RateLimitRule | None:
        if request.method != "POST":
            return None

        rules = {
            "/api/auth/login": RateLimitRule(
                method="POST",
                path="/api/auth/login",
                limit=settings.rate_limit_login_per_minute,
                window_seconds=60,
                name="auth-login",
            ),
            "/api/auth/signup": RateLimitRule(
                method="POST",
                path="/api/auth/signup",
                limit=settings.rate_limit_signup_per_hour,
                window_seconds=3600,
                name="auth-signup",
            ),
            "/api/auth/forgot-password": RateLimitRule(
                method="POST",
                path="/api/auth/forgot-password",
                limit=settings.rate_limit_forgot_password_per_hour,
                window_seconds=3600,
                name="auth-forgot-password",
            ),
            "/api/auth/reset-password": RateLimitRule(
                method="POST",
                path="/api/auth/reset-password",
                limit=settings.rate_limit_reset_password_per_hour,
                window_seconds=3600,
                name="auth-reset-password",
            ),
            "/api/auth/refresh": RateLimitRule(
                method="POST",
                path="/api/auth/refresh",
                limit=settings.rate_limit_refresh_per_minute,
                window_seconds=60,
                name="auth-refresh",
            ),
        }
        return rules.get(request.url.path)
