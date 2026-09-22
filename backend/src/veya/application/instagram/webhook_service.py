import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from veya.core.config import settings
from veya.domain.sync.models import InstagramSyncJob
from veya.repositories.instagram_accounts import InstagramAccountRepository
from veya.repositories.sync_jobs import InstagramSyncJobRepository


class InstagramWebhookError(RuntimeError):
    pass


class InstagramWebhookDisabledError(InstagramWebhookError):
    pass


class InstagramWebhookVerificationError(InstagramWebhookError):
    pass


class InstagramWebhookSignatureError(InstagramWebhookError):
    pass


@dataclass(frozen=True)
class InstagramWebhookPreparation:
    jobs: list[InstagramSyncJob]
    comment_events: int
    matched_accounts: int
    ignored_events: int


class InstagramWebhookService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.accounts = InstagramAccountRepository(db)
        self.jobs = InstagramSyncJobRepository(db)

    def ensure_enabled(self) -> None:
        if not settings.meta_webhook_enabled:
            raise InstagramWebhookDisabledError("Meta webhooks are disabled")

    def verification_challenge(
        self,
        *,
        mode: str,
        verify_token: str,
        challenge: str,
    ) -> str:
        self.ensure_enabled()

        if mode != "subscribe":
            raise InstagramWebhookVerificationError("Unsupported webhook verification mode")

        expected = settings.meta_webhook_verify_token
        if not expected or not hmac.compare_digest(verify_token, expected):
            raise InstagramWebhookVerificationError("Invalid webhook verification token")

        return challenge

    def verify_signature(self, *, body: bytes, signature: str | None) -> None:
        self.ensure_enabled()

        secret = settings.meta_webhook_app_secret or settings.instagram_client_secret
        if not secret or not signature or not signature.startswith("sha256="):
            raise InstagramWebhookSignatureError("Invalid webhook signature")

        digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        expected = f"sha256={digest}"

        if not hmac.compare_digest(signature, expected):
            raise InstagramWebhookSignatureError("Invalid webhook signature")

    def prepare_comment_sync_jobs(
        self,
        payload: dict[str, Any],
    ) -> InstagramWebhookPreparation:
        if payload.get("object") != "instagram":
            return InstagramWebhookPreparation(
                jobs=[],
                comment_events=0,
                matched_accounts=0,
                ignored_events=1,
            )

        external_account_ids: set[str] = set()
        comment_events = 0
        ignored_events = 0

        entries = payload.get("entry")
        if not isinstance(entries, list):
            entries = []

        for entry in entries:
            if not isinstance(entry, dict):
                ignored_events += 1
                continue

            instagram_user_id = str(entry.get("id") or "").strip()
            changes = entry.get("changes")
            if not isinstance(changes, list):
                ignored_events += 1
                continue

            for change in changes:
                if not isinstance(change, dict):
                    ignored_events += 1
                    continue

                if change.get("field") != "comments":
                    ignored_events += 1
                    continue

                comment_events += 1
                if instagram_user_id:
                    external_account_ids.add(instagram_user_id)
                else:
                    ignored_events += 1

        matched_accounts = []
        seen_account_ids: set[int] = set()

        for instagram_user_id in external_account_ids:
            for account in self.accounts.get_by_instagram_user_id(instagram_user_id):
                if account.id in seen_account_ids:
                    continue
                seen_account_ids.add(account.id)
                matched_accounts.append(account)

        now = datetime.now(timezone.utc)
        next_sync = now + timedelta(minutes=settings.background_sync_interval_minutes)
        jobs: list[InstagramSyncJob] = []

        for account in matched_accounts:
            if account.connection_status == "reconnect_required":
                continue

            if account.sync_status in {"queued", "running", "retrying"}:
                continue

            job = self.jobs.create(
                instagram_account_id=account.id,
                trigger="webhook",
            )
            account.sync_status = "queued"
            account.next_sync_at = next_sync
            account.last_sync_error = None
            jobs.append(job)

        self.db.commit()
        for job in jobs:
            self.db.refresh(job)

        return InstagramWebhookPreparation(
            jobs=jobs,
            comment_events=comment_events,
            matched_accounts=len(matched_accounts),
            ignored_events=ignored_events,
        )
