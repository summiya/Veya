import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone


request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_context.get()
        if request_id:
            payload["request_id"] = request_id

        for key in (
            "event",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "job_id",
            "account_id",
            "attempt_count",
            "error_type",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(*, level: str) -> None:
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root.addHandler(handler)
    root.setLevel(level.upper())

    # Keep third-party output useful without duplicating Uvicorn's own access log.
    logging.getLogger("uvicorn.access").disabled = True
