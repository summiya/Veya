import asyncio
import logging

from arq import Retry, cron
from arq.connections import RedisSettings
from arq.worker import func

from veya.application.background_sync.service import BackgroundSyncService
from veya.application.instagram.sync_service import InstagramSyncError
from veya.core.config import settings
from veya.core.logging import configure_logging
from veya.core.monitoring import (
    capture_exception,
    capture_operational_alert,
    initialize_error_monitoring,
)
from veya.core.runtime import validate_runtime_configuration
from veya.infrastructure.database.session import SessionLocal


logger = logging.getLogger("veya.worker")


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


def _cron_seconds() -> set[int] | int:
    interval = max(1, min(60, settings.background_sync_scheduler_seconds))
    if interval >= 60:
        return 0
    return set(range(0, 60, interval))


def _prepare_due_jobs() -> list[tuple[int, int]]:
    with SessionLocal() as db:
        jobs = BackgroundSyncService(db).prepare_due_jobs()
        return [(job.id, job.instagram_account_id) for job in jobs]


def _run_sync_job(job_id: int, attempt_count: int) -> dict[str, int]:
    with SessionLocal() as db:
        result = BackgroundSyncService(db).run_job(
            job_id=job_id,
            attempt_count=attempt_count,
        )
        return {
            "media_synced": result.media_synced,
            "comments_synced": result.comments_synced,
            "sentiment_analyzed": result.sentiment_analyzed,
            "safety_analyzed": result.safety_analyzed,
        }


def _mark_retrying(job_id: int, attempt_count: int, error_message: str) -> None:
    with SessionLocal() as db:
        BackgroundSyncService(db).mark_retrying(
            job_id=job_id,
            attempt_count=attempt_count,
            error_message=error_message,
        )


def _mark_failed(job_id: int, attempt_count: int, error_message: str) -> None:
    with SessionLocal() as db:
        BackgroundSyncService(db).mark_failed(
            job_id=job_id,
            attempt_count=attempt_count,
            error_message=error_message,
        )


def _mark_enqueue_failed(job_id: int, error_message: str) -> None:
    with SessionLocal() as db:
        BackgroundSyncService(db).mark_enqueue_failed(
            job_id=job_id,
            error_message=error_message,
        )


async def on_startup(ctx) -> None:
    configure_logging(level=settings.log_level)
    initialize_error_monitoring()
    validate_runtime_configuration()
    logger.info("Worker started", extra={"event": "worker_started"})


async def on_shutdown(ctx) -> None:
    logger.info("Worker stopped", extra={"event": "worker_stopped"})


async def enqueue_due_instagram_accounts(ctx) -> int:
    jobs = await asyncio.to_thread(_prepare_due_jobs)
    enqueued = 0

    for job_id, account_id in jobs:
        try:
            await ctx["redis"].enqueue_job(
                "sync_instagram_account",
                job_id,
                _job_id=f"veya-instagram-sync-{job_id}",
            )
            enqueued += 1
            logger.info(
                "Instagram sync job enqueued",
                extra={
                    "event": "instagram_sync_enqueued",
                    "job_id": job_id,
                    "account_id": account_id,
                },
            )
        except Exception as exc:
            await asyncio.to_thread(
                _mark_enqueue_failed,
                job_id,
                str(exc),
            )
            capture_exception(
                exc,
                event="instagram_sync_enqueue_failed",
                tags={
                    "job_id": job_id,
                    "account_id": account_id,
                },
            )
            logger.exception(
                "Instagram sync enqueue failed",
                extra={
                    "event": "instagram_sync_enqueue_failed",
                    "job_id": job_id,
                    "account_id": account_id,
                    "error_type": type(exc).__name__,
                },
            )

    return enqueued


async def sync_instagram_account(ctx, job_id: int) -> dict[str, int]:
    attempt_count = int(ctx.get("job_try", 1))
    logger.info(
        "Instagram sync job started",
        extra={
            "event": "instagram_sync_started",
            "job_id": job_id,
            "attempt_count": attempt_count,
        },
    )

    try:
        result = await asyncio.to_thread(_run_sync_job, job_id, attempt_count)
    except InstagramSyncError as exc:
        if exc.reconnect_required:
            await asyncio.to_thread(
                _mark_failed,
                job_id,
                attempt_count,
                str(exc),
            )
            capture_operational_alert(
                "Instagram account requires reconnection",
                event="instagram_reconnect_required",
                level="error",
                tags={
                    "job_id": job_id,
                    "attempt_count": attempt_count,
                },
                dedupe_key=f"instagram-reconnect:{job_id}",
            )
            logger.exception(
                "Instagram sync requires reconnect",
                extra={
                    "event": "instagram_sync_reconnect_required",
                    "job_id": job_id,
                    "attempt_count": attempt_count,
                    "error_type": type(exc).__name__,
                },
            )
            raise

        if attempt_count < settings.background_sync_max_retries:
            await asyncio.to_thread(
                _mark_retrying,
                job_id,
                attempt_count,
                str(exc),
            )
            logger.warning(
                "Instagram sync retry scheduled",
                extra={
                    "event": "instagram_sync_retry_scheduled",
                    "job_id": job_id,
                    "attempt_count": attempt_count,
                    "error_type": type(exc).__name__,
                },
            )
            raise Retry(
                defer=settings.background_sync_retry_seconds * attempt_count
            ) from exc

        await asyncio.to_thread(
            _mark_failed,
            job_id,
            attempt_count,
            str(exc),
        )
        capture_exception(
            exc,
            event="instagram_sync_failed",
            tags={
                "job_id": job_id,
                "attempt_count": attempt_count,
            },
        )
        logger.exception(
            "Instagram sync failed",
            extra={
                "event": "instagram_sync_failed",
                "job_id": job_id,
                "attempt_count": attempt_count,
                "error_type": type(exc).__name__,
            },
        )
        raise
    except Exception as exc:
        if attempt_count < settings.background_sync_max_retries:
            await asyncio.to_thread(
                _mark_retrying,
                job_id,
                attempt_count,
                str(exc),
            )
            logger.warning(
                "Background job retry scheduled",
                extra={
                    "event": "background_job_retry_scheduled",
                    "job_id": job_id,
                    "attempt_count": attempt_count,
                    "error_type": type(exc).__name__,
                },
            )
            raise Retry(
                defer=settings.background_sync_retry_seconds * attempt_count
            ) from exc

        await asyncio.to_thread(
            _mark_failed,
            job_id,
            attempt_count,
            str(exc),
        )
        capture_exception(
            exc,
            event="background_sync_failed",
            tags={
                "job_id": job_id,
                "attempt_count": attempt_count,
            },
        )
        logger.exception(
            "Background sync failed",
            extra={
                "event": "background_sync_failed",
                "job_id": job_id,
                "attempt_count": attempt_count,
                "error_type": type(exc).__name__,
            },
        )
        raise

    logger.info(
        "Instagram sync job completed",
        extra={
            "event": "instagram_sync_completed",
            "job_id": job_id,
            "attempt_count": attempt_count,
        },
    )
    return result


class WorkerSettings:
    redis_settings = _redis_settings()
    functions = [
        func(
            sync_instagram_account,
            max_tries=max(1, settings.background_sync_max_retries),
            keep_result=60,
        )
    ]
    cron_jobs = [
        cron(
            enqueue_due_instagram_accounts,
            second=_cron_seconds(),
            run_at_startup=True,
            unique=True,
        )
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = 4
    health_check_interval = 15
    health_check_key = "veya:worker:health"
