from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from veya.core.config import settings
from veya.domain.instagram.models import InstagramAccount, InstagramMedia
from veya.infrastructure.instagram.client import InstagramProfile, InstagramTokenResult
from veya.infrastructure.instagram.token_cipher import (
    decrypt_instagram_token,
    encrypt_instagram_token,
)
from veya.repositories.users import UserRepository


EMAIL = "production@example.com"
PASSWORD = "strong-password-123"


def signup(client: TestClient) -> dict:
    response = client.post(
        "/api/auth/signup",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth['access_token']}"}


def create_account(client: TestClient, db, *, expires_at=None) -> tuple[dict, InstagramAccount]:
    auth = signup(client)
    user = UserRepository(db).get_by_email(EMAIL)
    assert user is not None

    account = InstagramAccount(
        user_id=user.id,
        instagram_user_id="ig-production",
        username="creator",
        access_token_encrypted=encrypt_instagram_token("existing-token"),
        token_expires_at=expires_at,
        connection_status="connected",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return auth, account


def test_readiness_reports_required_meta_configuration(client: TestClient) -> None:
    auth = signup(client)

    response = client.get(
        "/api/integrations/instagram/readiness",
        headers=auth_headers(auth),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is True
    assert body["missing_settings"] == []
    assert "instagram_business_basic" in body["scopes"]
    assert "instagram_business_manage_comments" in body["scopes"]


def test_readiness_never_returns_secrets(client: TestClient) -> None:
    auth = signup(client)

    response = client.get(
        "/api/integrations/instagram/readiness",
        headers=auth_headers(auth),
    )

    serialized = response.text
    assert settings.instagram_client_secret not in serialized
    assert settings.instagram_token_encryption_key not in serialized


def test_connection_check_refreshes_token_near_expiry(
    client: TestClient,
    db,
    monkeypatch,
) -> None:
    auth, account = create_account(
        client,
        db,
        expires_at=datetime.now(timezone.utc) + timedelta(days=2),
    )
    account.last_token_refreshed_at = datetime.now(timezone.utc) - timedelta(days=10)
    db.commit()

    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.refresh_long_lived_token",
        lambda self, **kwargs: InstagramTokenResult(
            access_token="refreshed-token",
            instagram_user_id="ig-production",
            expires_at=datetime.now(timezone.utc) + timedelta(days=60),
        ),
    )
    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.get_profile",
        lambda self, access_token, instagram_user_id: InstagramProfile(
            instagram_user_id=instagram_user_id,
            username="updated_creator",
        ),
    )

    response = client.post(
        f"/api/integrations/instagram/accounts/{account.id}/check",
        headers=auth_headers(auth),
    )

    assert response.status_code == 200
    assert response.json()["token_refreshed"] is True
    assert response.json()["account"]["connection_status"] == "connected"

    db.refresh(account)
    assert decrypt_instagram_token(account.access_token_encrypted) == "refreshed-token"
    assert account.username == "updated_creator"
    assert account.last_connection_check_at is not None
    assert account.last_token_refreshed_at is not None


def test_expired_token_marks_account_for_reconnect(client: TestClient, db) -> None:
    auth, account = create_account(
        client,
        db,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    response = client.post(
        f"/api/integrations/instagram/accounts/{account.id}/check",
        headers=auth_headers(auth),
    )

    assert response.status_code == 409

    db.refresh(account)
    assert account.connection_status == "reconnect_required"
    assert account.next_sync_at is None
    assert account.last_api_error_code == "token_expired"


def test_disconnect_removes_account_and_imported_data(client: TestClient, db) -> None:
    auth, account = create_account(client, db)
    db.add(
        InstagramMedia(
            instagram_account_id=account.id,
            instagram_media_id="media-delete",
            media_type="IMAGE",
            caption="Delete me",
        )
    )
    db.commit()

    response = client.delete(
        f"/api/integrations/instagram/accounts/{account.id}",
        headers=auth_headers(auth),
    )

    assert response.status_code == 200
    db.expire_all()
    assert db.get(InstagramAccount, account.id) is None
    assert db.query(InstagramMedia).count() == 0


def test_reconnect_required_account_is_not_scheduled(client: TestClient, db) -> None:
    _, account = create_account(client, db)
    account.connection_status = "reconnect_required"
    account.next_sync_at = None
    db.commit()

    from veya.application.background_sync.service import BackgroundSyncService

    assert BackgroundSyncService(db).prepare_due_jobs() == []
