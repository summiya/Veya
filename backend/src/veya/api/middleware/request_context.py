import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from veya.core.logging import request_id_context


logger = logging.getLogger("veya.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("x-request-id", "").strip()
        request_id = incoming[:128] if incoming else str(uuid.uuid4())
        token = request_id_context.set(request_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.exception(
                "Unhandled request error",
                extra={
                    "event": "http_request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error_type": type(exc).__name__,
                },
            )
            raise
        else:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "Request completed",
                extra={
                    "event": "http_request_completed",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_context.reset(token)
