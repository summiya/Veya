from veya.core import monitoring
from veya.core.config import settings
from veya.core.logging import request_id_context


def test_scrub_sentry_event_removes_sensitive_request_data() -> None:
    event = {
        "request": {
            "url": "https://app.example.com/reset-password?token=secret-token",
            "query_string": "token=secret-token",
            "data": {"password": "secret"},
            "cookies": {"session": "secret"},
            "headers": {
                "Authorization": "Bearer secret",
                "Cookie": "session=secret",
                "X-Request-ID": "request-123",
            },
        },
        "user": {"email": "creator@example.com"},
    }

    token = request_id_context.set("request-123")
    try:
        scrubbed = monitoring.scrub_sentry_event(event)
    finally:
        request_id_context.reset(token)

    assert scrubbed["request"]["url"] == "https://app.example.com/reset-password"
    assert scrubbed["request"]["query_string"] == ""
    assert scrubbed["request"]["data"] is None
    assert scrubbed["request"]["cookies"] is None
    assert "Authorization" not in scrubbed["request"]["headers"]
    assert "Cookie" not in scrubbed["request"]["headers"]
    assert "user" not in scrubbed
    assert scrubbed["tags"]["request_id"] == "request-123"


def test_scrub_breadcrumb_removes_query_and_tokens() -> None:
    breadcrumb = {
        "data": {
            "url": "https://app.example.com/reset-password?token=secret",
            "access_token": "secret",
        }
    }

    scrubbed = monitoring.scrub_sentry_breadcrumb(breadcrumb)

    assert scrubbed["data"]["url"] == "https://app.example.com/reset-password"
    assert scrubbed["data"]["access_token"] == "[Filtered]"


def test_operational_alert_is_deduplicated(monkeypatch) -> None:
    messages: list[str] = []
    original_dsn = settings.sentry_dsn

    try:
        settings.sentry_dsn = "https://public@example.invalid/1"
        monitoring._last_alert_at.clear()
        monkeypatch.setattr(
            monitoring.sentry_sdk,
            "capture_message",
            lambda message, level: messages.append(message),
        )

        first = monitoring.capture_operational_alert(
            "Readiness degraded",
            event="readiness_degraded",
            dedupe_key="health",
            cooldown_seconds=300,
        )
        second = monitoring.capture_operational_alert(
            "Readiness degraded",
            event="readiness_degraded",
            dedupe_key="health",
            cooldown_seconds=300,
        )
    finally:
        settings.sentry_dsn = original_dsn
        monitoring._last_alert_at.clear()

    assert first is True
    assert second is False
    assert messages == ["Readiness degraded"]


def test_monitoring_is_disabled_without_dsn() -> None:
    original_dsn = settings.sentry_dsn
    try:
        settings.sentry_dsn = ""
        assert monitoring.initialize_error_monitoring() is False
        assert (
            monitoring.capture_operational_alert(
                "ignored",
                event="ignored",
            )
            is False
        )
    finally:
        settings.sentry_dsn = original_dsn
