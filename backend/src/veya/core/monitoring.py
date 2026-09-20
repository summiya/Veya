import threading
import time
from collections.abc import Mapping
from typing import Any

import sentry_sdk

from veya.core.config import settings
from veya.core.logging import request_id_context


_alert_lock = threading.Lock()
_last_alert_at: dict[str, float] = {}


SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
}


def _strip_url_query(value: str | None) -> str | None:
    if not value or "?" not in value:
        return value
    return value.split("?", 1)[0]


def scrub_sentry_event(event: dict[str, Any], hint: dict[str, Any] | None = None):
    request = event.get("request")
    if isinstance(request, dict):
        request["url"] = _strip_url_query(request.get("url"))
        request["query_string"] = ""
        request["data"] = None
        request["cookies"] = None

        headers = request.get("headers")
        if isinstance(headers, Mapping):
            request["headers"] = {
                key: value
                for key, value in headers.items()
                if str(key).lower() not in SENSITIVE_HEADERS
            }

    # Veya does not need user identity/PII in error monitoring.
    event.pop("user", None)

    tags = event.setdefault("tags", {})
    request_id = request_id_context.get()
    if request_id:
        tags["request_id"] = request_id

    return event


def scrub_sentry_breadcrumb(
    breadcrumb: dict[str, Any],
    hint: dict[str, Any] | None = None,
):
    data = breadcrumb.get("data")
    if isinstance(data, dict):
        if "url" in data:
            data["url"] = _strip_url_query(data.get("url"))

        for key in list(data):
            if str(key).lower() in {
                "authorization",
                "cookie",
                "password",
                "token",
                "access_token",
                "refresh_token",
            }:
                data[key] = "[Filtered]"

    return breadcrumb


def initialize_error_monitoring() -> bool:
    if not settings.sentry_dsn:
        return False

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.service_version,
        traces_sample_rate=max(0.0, min(1.0, settings.sentry_traces_sample_rate)),
        send_default_pii=False,
        before_send=scrub_sentry_event,
        before_breadcrumb=scrub_sentry_breadcrumb,
    )
    return True


def capture_exception(
    error: BaseException,
    *,
    event: str,
    tags: Mapping[str, object] | None = None,
) -> None:
    if not settings.sentry_dsn:
        return

    with sentry_sdk.new_scope() as scope:
        scope.set_tag("event", event)
        for key, value in (tags or {}).items():
            scope.set_tag(key, str(value))
        request_id = request_id_context.get()
        if request_id:
            scope.set_tag("request_id", request_id)
        sentry_sdk.capture_exception(error)


def capture_operational_alert(
    message: str,
    *,
    event: str,
    level: str = "warning",
    tags: Mapping[str, object] | None = None,
    dedupe_key: str | None = None,
    cooldown_seconds: int | None = None,
) -> bool:
    if not settings.sentry_dsn:
        return False

    key = dedupe_key or f"{event}:{message}"
    cooldown = (
        settings.sentry_alert_cooldown_seconds
        if cooldown_seconds is None
        else cooldown_seconds
    )
    now = time.monotonic()

    with _alert_lock:
        previous = _last_alert_at.get(key)
        if previous is not None and now - previous < cooldown:
            return False
        _last_alert_at[key] = now

    with sentry_sdk.new_scope() as scope:
        scope.set_tag("event", event)
        for key_name, value in (tags or {}).items():
            scope.set_tag(key_name, str(value))
        sentry_sdk.capture_message(message, level=level)

    return True
