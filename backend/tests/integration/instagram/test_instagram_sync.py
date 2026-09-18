from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from veya.domain.instagram.models import InstagramComment, InstagramMedia
from veya.infrastructure.instagram.client import InstagramCommentItem, InstagramMediaItem
from veya.infrastructure.instagram.token_cipher import encrypt_instagram_token
from veya.repositories.instagram_accounts import InstagramAccountRepository
from veya.repositories.users import UserRepository


EMAIL = "creator@example.com"
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


def create_connected_account(client: TestClient, db) -> tuple[dict, int]:
    auth = signup(client)
    user = UserRepository(db).get_by_email(EMAIL)
    assert user is not None

    account = InstagramAccountRepository(db).upsert(
        user_id=user.id,
        instagram_user_id="ig-user-1",
        username="creator",
        access_token_encrypted=encrypt_instagram_token("fake-access-token"),
        token_expires_at=None,
    )
    db.commit()
    db.refresh(account)
    return auth, account.id


def test_sync_persists_media_and_comments(client: TestClient, db, monkeypatch) -> None:
    auth, account_id = create_connected_account(client, db)

    media = [
        InstagramMediaItem(
            media_id="media-1",
            media_type="REELS",
            caption="Dubai reel",
            media_url="https://example.com/media.mp4",
            thumbnail_url="https://example.com/thumb.jpg",
            permalink="https://instagram.com/p/media-1",
            timestamp=datetime(2026, 9, 18, tzinfo=timezone.utc),
        )
    ]
    comments = [
        InstagramCommentItem(
            comment_id="comment-1",
            text="Love this!",
            username="viewer",
            timestamp=datetime(2026, 9, 18, 1, tzinfo=timezone.utc),
        ),
        InstagramCommentItem(
            comment_id="comment-2",
            text="Where is this?",
            username="traveler",
            timestamp=datetime(2026, 9, 18, 2, tzinfo=timezone.utc),
        ),
    ]

    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.list_media",
        lambda self, **kwargs: media,
    )
    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.list_comments",
        lambda self, **kwargs: comments,
    )

    response = client.post(
        f"/api/integrations/instagram/accounts/{account_id}/sync",
        headers=auth_headers(auth),
    )

    assert response.status_code == 200
    assert response.json() == {"media_count": 1, "comment_count": 2}

    stored_media = list(db.scalars(select(InstagramMedia)))
    stored_comments = list(db.scalars(select(InstagramComment)))
    assert len(stored_media) == 1
    assert stored_media[0].caption == "Dubai reel"
    assert len(stored_comments) == 2


def test_sync_is_idempotent(client: TestClient, db, monkeypatch) -> None:
    auth, account_id = create_connected_account(client, db)

    media = [
        InstagramMediaItem(
            media_id="media-1",
            media_type="IMAGE",
            caption="First caption",
            media_url=None,
            thumbnail_url=None,
            permalink=None,
            timestamp=None,
        )
    ]
    comments = [
        InstagramCommentItem(
            comment_id="comment-1",
            text="First text",
            username="viewer",
            timestamp=None,
        )
    ]

    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.list_media",
        lambda self, **kwargs: media,
    )
    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.list_comments",
        lambda self, **kwargs: comments,
    )

    first = client.post(
        f"/api/integrations/instagram/accounts/{account_id}/sync",
        headers=auth_headers(auth),
    )
    assert first.status_code == 200

    media[0] = InstagramMediaItem(
        media_id="media-1",
        media_type="IMAGE",
        caption="Updated caption",
        media_url=None,
        thumbnail_url=None,
        permalink=None,
        timestamp=None,
    )
    comments[0] = InstagramCommentItem(
        comment_id="comment-1",
        text="Updated text",
        username="viewer",
        timestamp=None,
    )

    second = client.post(
        f"/api/integrations/instagram/accounts/{account_id}/sync",
        headers=auth_headers(auth),
    )
    assert second.status_code == 200

    stored_media = list(db.scalars(select(InstagramMedia)))
    stored_comments = list(db.scalars(select(InstagramComment)))
    assert len(stored_media) == 1
    assert stored_media[0].caption == "Updated caption"
    assert len(stored_comments) == 1
    assert stored_comments[0].text == "Updated text"


def test_media_and_comments_read_apis(client: TestClient, db, monkeypatch) -> None:
    auth, account_id = create_connected_account(client, db)

    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.list_media",
        lambda self, **kwargs: [
            InstagramMediaItem(
                media_id="media-1",
                media_type="IMAGE",
                caption="Hello",
                media_url=None,
                thumbnail_url=None,
                permalink=None,
                timestamp=None,
            )
        ],
    )
    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.list_comments",
        lambda self, **kwargs: [
            InstagramCommentItem(
                comment_id="comment-1",
                text="Great",
                username="viewer",
                timestamp=None,
            )
        ],
    )

    sync = client.post(
        f"/api/integrations/instagram/accounts/{account_id}/sync",
        headers=auth_headers(auth),
    )
    assert sync.status_code == 200

    media_response = client.get(
        f"/api/integrations/instagram/accounts/{account_id}/media",
        headers=auth_headers(auth),
    )
    assert media_response.status_code == 200
    media_id = media_response.json()[0]["id"]

    comments_response = client.get(
        f"/api/integrations/instagram/accounts/{account_id}/media/{media_id}/comments",
        headers=auth_headers(auth),
    )

    assert comments_response.status_code == 200
    assert comments_response.json()[0]["text"] == "Great"


def test_sync_rejects_account_owned_by_another_user(client: TestClient, db) -> None:
    first_auth, account_id = create_connected_account(client, db)

    second_signup = client.post(
        "/api/auth/signup",
        json={"email": "second@example.com", "password": PASSWORD},
    )
    assert second_signup.status_code == 201

    response = client.post(
        f"/api/integrations/instagram/accounts/{account_id}/sync",
        headers=auth_headers(second_signup.json()),
    )

    assert response.status_code == 400
    assert first_auth["user"]["email"] == EMAIL
