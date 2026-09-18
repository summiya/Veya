import asyncio

from arq import Retry, cron
from arq.connections import RedisSettings
from arq.worker import func

from veya.application.background_sync.service import BackgroundSyncService
from veya.core.config import settings
from veya.infrastructure.database.session import SessionLocal


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


async def enqueue_due_instagram_accounts(ctx) -> int:
    jobs = await asyncio.to_thread(_prepare_due_jobs)
    enqueued = 0

    for job_id, _account_id in jobs:
        try:
            await ctx["redis"].enqueue_job(
                "sync_instagram_account",
                job_id,
                _job_id=f"veya-instagram-sync-{job_id}",
            )
            enqueued += 1
        except Exception as exc:
            await asyncio.to_thread(
                _mark_enqueue_failed,
                job_id,
                str(exc),
            )

    return enqueued


async def sync_instagram_account(ctx, job_id: int) -> dict[str, int]:
    attempt_count = int(ctx.get("job_try", 1))

    try:
        return await asyncio.to_thread(_run_sync_job, job_id, attempt_count)
    except Exception as exc:
        if attempt_count < settings.background_sync_max_retries:
            await asyncio.to_thread(
                _mark_retrying,
                job_id,
                attempt_count,
                str(exc),
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
        raise


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
    max_jobs = 4
    health_check_interval = 15
    health_check_key = "veya:worker:health"
