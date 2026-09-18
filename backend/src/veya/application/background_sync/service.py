from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from veya.application.analytics.service import AnalyticsService
from veya.application.instagram.sync_service import InstagramSyncService
from veya.application.safety.service import SafetyService
from veya.application.sentiment.service import SentimentService
from veya.core.config import settings
from veya.domain.sync.models import InstagramSyncJob
from veya.domain.users.models import User
from veya.repositories.instagram_accounts import InstagramAccountRepository
from veya.repositories.sync_jobs import InstagramSyncJobRepository


class BackgroundSyncError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackgroundSyncRunResult:
    media_synced: int
    comments_synced: int
    sentiment_analyzed: int
    safety_analyzed: int


class BackgroundSyncService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.accounts = InstagramAccountRepository(db)
        self.jobs = InstagramSyncJobRepository(db)

    def prepare_due_jobs(self) -> list[InstagramSyncJob]:
        now = datetime.now(timezone.utc)
        next_sync = now + timedelta(minutes=settings.background_sync_interval_minutes)
        jobs: list[InstagramSyncJob] = []

        for account in self.accounts.list_due_for_sync(now):
            job = self.jobs.create(
                instagram_account_id=account.id,
                trigger="scheduled",
            )
            account.sync_status = "queued"
            account.next_sync_at = next_sync
            account.last_sync_error = None
            jobs.append(job)

        self.db.commit()
        for job in jobs:
            self.db.refresh(job)
        return jobs

    def run_job(
        self,
        *,
        job_id: int,
        attempt_count: int,
    ) -> BackgroundSyncRunResult:
        job = self.jobs.get_by_id(job_id)
        if job is None:
            raise BackgroundSyncError("Background sync job not found")

        account = self.accounts.get_by_id(job.instagram_account_id)
        if account is None:
            raise BackgroundSyncError("Instagram account not found")

        user: User = account.user
        self.jobs.mark_running(job, attempt_count=attempt_count)
        account.sync_status = "running"
        account.last_sync_error = None
        self.db.commit()

        sync_result = InstagramSyncService(self.db).sync_account(
            user=user,
            account_id=account.id,
        )
        sentiment_result = SentimentService(self.db).analyze_pending_account(
            user=user,
            account_id=account.id,
        )
        safety_result = SafetyService(self.db).analyze_pending_account(
            user=user,
            account_id=account.id,
        )
        AnalyticsService(self.db).capture_snapshot(
            user=user,
            account_id=account.id,
        )

        now = datetime.now(timezone.utc)
        account = self.accounts.get_by_id(account.id)
        job = self.jobs.get_by_id(job.id)
        if account is None or job is None:
            raise BackgroundSyncError("Background sync state disappeared")

        self.jobs.mark_completed(
            job,
            media_synced=sync_result.media_count,
            comments_synced=sync_result.comment_count,
            sentiment_analyzed=sentiment_result.analyzed_comments,
            safety_analyzed=safety_result.analyzed_comments,
        )
        account.sync_status = "idle"
        account.last_synced_at = now
        account.next_sync_at = now + timedelta(
            minutes=settings.background_sync_interval_minutes
        )
        account.last_sync_error = None
        self.db.commit()

        return BackgroundSyncRunResult(
            media_synced=sync_result.media_count,
            comments_synced=sync_result.comment_count,
            sentiment_analyzed=sentiment_result.analyzed_comments,
            safety_analyzed=safety_result.analyzed_comments,
        )

    def mark_retrying(
        self,
        *,
        job_id: int,
        attempt_count: int,
        error_message: str,
    ) -> None:
        job = self.jobs.get_by_id(job_id)
        if job is None:
            return
        account = self.accounts.get_by_id(job.instagram_account_id)
        self.jobs.mark_retrying(
            job,
            attempt_count=attempt_count,
            error_message=error_message,
        )
        if account is not None:
            account.sync_status = "retrying"
            account.last_sync_error = error_message[:4000]
        self.db.commit()

    def mark_failed(
        self,
        *,
        job_id: int,
        attempt_count: int,
        error_message: str,
    ) -> None:
        job = self.jobs.get_by_id(job_id)
        if job is None:
            return
        account = self.accounts.get_by_id(job.instagram_account_id)
        self.jobs.mark_failed(
            job,
            attempt_count=attempt_count,
            error_message=error_message,
        )
        if account is not None:
            account.sync_status = "failed"
            account.last_sync_error = error_message[:4000]
            account.next_sync_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.background_sync_interval_minutes
            )
        self.db.commit()

    def mark_enqueue_failed(self, *, job_id: int, error_message: str) -> None:
        self.mark_failed(
            job_id=job_id,
            attempt_count=0,
            error_message=f"Queue enqueue failed: {error_message}",
        )

    def list_jobs(
        self,
        *,
        user: User,
        account_id: int,
        limit: int = 20,
    ) -> list[InstagramSyncJob]:
        account = next(
            (
                item
                for item in self.accounts.get_by_user_id(user.id)
                if item.id == account_id
            ),
            None,
        )
        if account is None:
            raise BackgroundSyncError("Instagram account not found")
        return self.jobs.list_for_account(account.id, limit=limit)
