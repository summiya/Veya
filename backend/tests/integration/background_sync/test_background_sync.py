from datetime import datetime, timezone

from veya.application.analytics.service import AnalyticsService
from veya.application.background_sync.service import BackgroundSyncService
from veya.application.instagram.sync_service import InstagramSyncResult, InstagramSyncService
from veya.application.safety.service import SafetyAnalyzeResult, SafetyService
from veya.application.sentiment.service import AnalyzeSentimentResult, SentimentService
from veya.domain.instagram.models import InstagramAccount
from veya.infrastructure.instagram.token_cipher import encrypt_instagram_token
from veya.repositories.users import UserRepository


EMAIL = "creator@example.com"
PASSWORD = "strong-password-123"


def create_account(client, db) -> tuple[dict, InstagramAccount]:
    auth = client.post(
        "/api/auth/signup",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert auth.status_code == 201

    user = UserRepository(db).get_by_email(EMAIL)
    assert user is not None

    account = InstagramAccount(
        user_id=user.id,
        instagram_user_id="ig-background",
        username="creator",
        access_token_encrypted=encrypt_instagram_token("fake-access-token"),
        token_expires_at=None,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return auth.json(), account


def test_prepare_due_jobs_claims_account_once(client, db) -> None:
    _, account = create_account(client, db)
    service = BackgroundSyncService(db)

    first = service.prepare_due_jobs()
    second = service.prepare_due_jobs()

    assert len(first) == 1
    assert second == []

    db.refresh(account)
    assert account.sync_status == "queued"
    assert account.next_sync_at is not None
    assert first[0].status == "queued"
    assert first[0].trigger == "scheduled"


def test_run_job_completes_full_pipeline(client, db, monkeypatch) -> None:
    _, account = create_account(client, db)
    service = BackgroundSyncService(db)
    job = service.prepare_due_jobs()[0]

    monkeypatch.setattr(
        InstagramSyncService,
        "sync_account",
        lambda self, **kwargs: InstagramSyncResult(media_count=2, comment_count=5),
    )
    monkeypatch.setattr(
        SentimentService,
        "analyze_pending_account",
        lambda self, **kwargs: AnalyzeSentimentResult(analyzed_comments=3),
    )
    monkeypatch.setattr(
        SafetyService,
        "analyze_pending_account",
        lambda self, **kwargs: SafetyAnalyzeResult(analyzed_comments=3),
    )
    monkeypatch.setattr(
        AnalyticsService,
        "capture_snapshot",
        lambda self, **kwargs: None,
    )

    result = service.run_job(job_id=job.id, attempt_count=1)

    db.refresh(job)
    db.refresh(account)

    assert result.media_synced == 2
    assert result.comments_synced == 5
    assert result.sentiment_analyzed == 3
    assert result.safety_analyzed == 3
    assert job.status == "completed"
    assert job.media_synced == 2
    assert job.comments_synced == 5
    assert account.sync_status == "idle"
    assert account.last_synced_at is not None
    assert account.next_sync_at is not None
    assert account.last_sync_error is None


def test_retry_and_failure_state_are_persisted(client, db) -> None:
    _, account = create_account(client, db)
    service = BackgroundSyncService(db)
    job = service.prepare_due_jobs()[0]

    service.mark_retrying(
        job_id=job.id,
        attempt_count=1,
        error_message="temporary error",
    )
    db.refresh(job)
    db.refresh(account)

    assert job.status == "retrying"
    assert account.sync_status == "retrying"
    assert account.last_sync_error == "temporary error"

    service.mark_failed(
        job_id=job.id,
        attempt_count=3,
        error_message="permanent error",
    )
    db.refresh(job)
    db.refresh(account)

    assert job.status == "failed"
    assert job.completed_at is not None
    assert account.sync_status == "failed"
    assert account.last_sync_error == "permanent error"
    assert account.next_sync_at is not None


def test_job_history_api_is_scoped_to_account_owner(client, db) -> None:
    auth, account = create_account(client, db)
    service = BackgroundSyncService(db)
    service.prepare_due_jobs()

    response = client.get(
        f"/api/background-sync/instagram/accounts/{account.id}/jobs",
        headers={"Authorization": f"Bearer {auth['access_token']}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "queued"

    other = client.post(
        "/api/auth/signup",
        json={"email": "other@example.com", "password": PASSWORD},
    )
    assert other.status_code == 201

    forbidden = client.get(
        f"/api/background-sync/instagram/accounts/{account.id}/jobs",
        headers={"Authorization": f"Bearer {other.json()['access_token']}"},
    )
    assert forbidden.status_code == 404
