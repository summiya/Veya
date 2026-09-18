from dataclasses import dataclass

from redis import Redis
from sqlalchemy import text

from veya.core.config import settings
from veya.infrastructure.database.session import engine


@dataclass(frozen=True)
class DependencyHealth:
    status: str
    database: str
    redis: str


class HealthService:
    def check(self) -> DependencyHealth:
        database_status = self._database_status()
        redis_status = self._redis_status()
        overall = (
            "ok"
            if database_status == "ok" and redis_status == "ok"
            else "degraded"
        )
        return DependencyHealth(
            status=overall,
            database=database_status,
            redis=redis_status,
        )

    @staticmethod
    def _database_status() -> str:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return "ok"
        except Exception:
            return "unavailable"

    @staticmethod
    def _redis_status() -> str:
        client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        try:
            return "ok" if client.ping() else "unavailable"
        except Exception:
            return "unavailable"
        finally:
            client.close()
