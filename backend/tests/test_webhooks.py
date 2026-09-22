import hashlib
import hmac
import json

from sqlalchemy import select

from veya.core.config import settings
from veya.domain.instagram.models import InstagramAccount
from veya.domain.sync.models import InstagramSyncJob
from veya.domain.users.models import User


class FakeRedis:
    def __init__(self) -> None:
        self.claimed: set[str] = set()
        self.enqueued: list[tuple[str, tuple, dict]] = []
        self.deleted: list[str] = []

    async def set(self, key, value, *, ex=None, nx=False):
        if nx and key in self.claimed:
            return False
        self.claimed.add(key)
        return True

    async def enqueue_job(self, name, *args, **kwargs):
        self.enqueued.append((name, args, kwargs))
        return object()

    async def delete(self, key):
        self.claimed.discard(key)
        self.deleted.append(key)
        return 1

    async def aclose(self):
        return None


def _signature(body: bytes) -> str:
    digest = hmac.new(
        settings.meta_webhook_app_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


def _seed_instagram_account(db, *, instagram_user_id: str = "178900000000001"):
    user = User(
        email="webhook-creator@example.com",
        password_hash="not-used-in-this-test",
    )
    db.add(user)
    db.flush()

    account = InstagramAccount(
        user_id=user.id,
        instagram_user_id=instagram_user_id,
        username="webhook_creator",
        access_token_encrypted="encrypted-token-placeholder",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def _comment_payload(instagram_user_id: str) -> dict:
    return {
        "object": "instagram",
        "entry": [
            {
                "id": instagram_user_id,
                "time": 1789910400,
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "id": "comment-123",
                            "text": "Love this post",
                            "media": {"id": "media-123"},
                        },
                    }
                ],
            }
        ],
    }


def test_webhook_verification_returns_challenge(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "meta_webhook_enabled", True)
    monkeypatch.setattr(settings, "meta_webhook_verify_token", "verify-me")

    response = client.get(
        "/api/webhooks/meta/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-me",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 200
    assert response.text == "challenge-123"


def test_webhook_verification_rejects_bad_token(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "meta_webhook_enabled", True)
    monkeypatch.setattr(settings, "meta_webhook_verify_token", "verify-me")

    response = client.get(
        "/api/webhooks/meta/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 403


def test_webhook_rejects_invalid_signature(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "meta_webhook_enabled", True)
    monkeypatch.setattr(settings, "meta_webhook_app_secret", "webhook-secret")

    raw = json.dumps(_comment_payload("178900000000001")).encode()

    response = client.post(
        "/api/webhooks/meta/instagram",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=invalid",
        },
    )

    assert response.status_code == 401


def test_comment_webhook_queues_existing_sync_pipeline(
    client,
    db,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "meta_webhook_enabled", True)
    monkeypatch.setattr(settings, "meta_webhook_app_secret", "webhook-secret")
    redis = FakeRedis()

    async def fake_create_pool(*args, **kwargs):
        return redis

    monkeypatch.setattr("veya.api.routes.webhooks.create_pool", fake_create_pool)

    account = _seed_instagram_account(db)
    raw = json.dumps(
        _comment_payload(account.instagram_user_id),
        separators=(",", ":"),
    ).encode()

    response = client.post(
        "/api/webhooks/meta/instagram",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": _signature(raw),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "comment_events": 1,
        "matched_accounts": 1,
        "queued_jobs": 1,
        "ignored_events": 0,
    }

    jobs = list(db.scalars(select(InstagramSyncJob)))
    assert len(jobs) == 1
    assert jobs[0].instagram_account_id == account.id
    assert jobs[0].trigger == "webhook"
    assert jobs[0].status == "queued"
    assert redis.enqueued[0][0] == "sync_instagram_account"
    assert redis.enqueued[0][1] == (jobs[0].id,)


def test_duplicate_webhook_delivery_is_not_queued_twice(
    client,
    db,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "meta_webhook_enabled", True)
    monkeypatch.setattr(settings, "meta_webhook_app_secret", "webhook-secret")
    redis = FakeRedis()

    async def fake_create_pool(*args, **kwargs):
        return redis

    monkeypatch.setattr("veya.api.routes.webhooks.create_pool", fake_create_pool)

    account = _seed_instagram_account(db)
    raw = json.dumps(
        _comment_payload(account.instagram_user_id),
        separators=(",", ":"),
    ).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": _signature(raw),
    }

    first = client.post("/api/webhooks/meta/instagram", content=raw, headers=headers)
    second = client.post("/api/webhooks/meta/instagram", content=raw, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert len(list(db.scalars(select(InstagramSyncJob)))) == 1
    assert len(redis.enqueued) == 1


def test_non_comment_webhook_is_acknowledged_without_sync(
    client,
    db,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "meta_webhook_enabled", True)
    monkeypatch.setattr(settings, "meta_webhook_app_secret", "webhook-secret")
    redis = FakeRedis()

    async def fake_create_pool(*args, **kwargs):
        return redis

    monkeypatch.setattr("veya.api.routes.webhooks.create_pool", fake_create_pool)

    raw = json.dumps(
        {
            "object": "instagram",
            "entry": [
                {
                    "id": "178900000000001",
                    "changes": [{"field": "mentions", "value": {"id": "media-1"}}],
                }
            ],
        },
        separators=(",", ":"),
    ).encode()

    response = client.post(
        "/api/webhooks/meta/instagram",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": _signature(raw),
        },
    )

    assert response.status_code == 200
    assert response.json()["queued_jobs"] == 0
    assert response.json()["ignored_events"] == 1
    assert list(db.scalars(select(InstagramSyncJob))) == []
