from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from veya.domain.sync.models import InstagramSyncJob


class InstagramSyncJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        instagram_account_id: int,
        trigger: str,
    ) -> InstagramSyncJob:
        job = InstagramSyncJob(
            instagram_account_id=instagram_account_id,
            status="queued",
            trigger=trigger,
        )
        self.db.add(job)
        self.db.flush()
        return job

    def get_by_id(self, job_id: int) -> InstagramSyncJob | None:
        return self.db.get(InstagramSyncJob, job_id)

    def list_for_account(
        self,
        instagram_account_id: int,
        *,
        limit: int = 20,
    ) -> list[InstagramSyncJob]:
        return list(
            self.db.scalars(
                select(InstagramSyncJob)
                .where(InstagramSyncJob.instagram_account_id == instagram_account_id)
                .order_by(InstagramSyncJob.id.desc())
                .limit(limit)
            )
        )

    def mark_running(self, job: InstagramSyncJob, *, attempt_count: int) -> None:
        job.status = "running"
        job.attempt_count = attempt_count
        job.error_message = None
        job.started_at = datetime.now(timezone.utc)
        job.completed_at = None
        self.db.flush()

    def mark_retrying(
        self,
        job: InstagramSyncJob,
        *,
        attempt_count: int,
        error_message: str,
    ) -> None:
        job.status = "retrying"
        job.attempt_count = attempt_count
        job.error_message = error_message[:4000]
        self.db.flush()

    def mark_completed(
        self,
        job: InstagramSyncJob,
        *,
        media_synced: int,
        comments_synced: int,
        sentiment_analyzed: int,
        safety_analyzed: int,
    ) -> None:
        job.status = "completed"
        job.media_synced = media_synced
        job.comments_synced = comments_synced
        job.sentiment_analyzed = sentiment_analyzed
        job.safety_analyzed = safety_analyzed
        job.error_message = None
        job.completed_at = datetime.now(timezone.utc)
        self.db.flush()

    def mark_failed(
        self,
        job: InstagramSyncJob,
        *,
        attempt_count: int,
        error_message: str,
    ) -> None:
        job.status = "failed"
        job.attempt_count = attempt_count
        job.error_message = error_message[:4000]
        job.completed_at = datetime.now(timezone.utc)
        self.db.flush()
