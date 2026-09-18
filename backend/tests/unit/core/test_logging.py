import json
import logging

from veya.core.logging import JsonFormatter, request_id_context


def test_json_formatter_includes_request_context_and_event_fields() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="veya.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Request completed",
        args=(),
        exc_info=None,
    )
    record.event = "http_request_completed"
    record.method = "GET"
    record.path = "/health/live"
    record.status_code = 200
    record.duration_ms = 12.5

    token = request_id_context.set("request-abc")
    try:
        payload = json.loads(formatter.format(record))
    finally:
        request_id_context.reset(token)

    assert payload["level"] == "INFO"
    assert payload["request_id"] == "request-abc"
    assert payload["event"] == "http_request_completed"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health/live"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 12.5
