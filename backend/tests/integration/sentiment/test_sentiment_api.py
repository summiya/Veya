from sqlalchemy import select

from veya.domain.instagram.models import InstagramAccount, InstagramComment, InstagramMedia
from veya.domain.sentiment.models import CommentSentiment
from veya.infrastructure.instagram.token_cipher import encrypt_instagram_token
from veya.repositories.users import UserRepository


EMAIL = "creator@example.com"
PASSWORD = "strong-password-123"


def signup(client) -> dict:
    response = client.post(
        "/api/auth/signup",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth['access_token']}"}


def seed_account_with_comments(client, db) -> tuple[dict, int, int]:
    auth = signup(client)
    user = UserRepository(db).get_by_email(EMAIL)
    assert user is not None

    account = InstagramAccount(
        user_id=user.id,
        instagram_user_id="ig-user-1",
        username="creator",
        access_token_encrypted=encrypt_instagram_token("fake-access-token"),
        token_expires_at=None,
    )
    db.add(account)
    db.flush()

    media = InstagramMedia(
        instagram_account_id=account.id,
        instagram_media_id="media-1",
        media_type="REELS",
        caption="Test reel",
    )
    db.add(media)
    db.flush()

    db.add_all(
        [
            InstagramComment(
                instagram_media_id=media.id,
                instagram_comment_id="comment-1",
                text="I love this!",
                username="viewer1",
            ),
            InstagramComment(
                instagram_media_id=media.id,
                instagram_comment_id="comment-2",
                text="This is awful.",
                username="viewer2",
            ),
            InstagramComment(
                instagram_media_id=media.id,
                instagram_comment_id="comment-3",
                text="The video was uploaded today.",
                username="viewer3",
            ),
        ]
    )
    db.commit()
    return auth, account.id, media.id


def test_analyze_account_persists_one_sentiment_per_comment(client, db) -> None:
    auth, account_id, _ = seed_account_with_comments(client, db)

    first = client.post(
        f"/api/sentiment/instagram/accounts/{account_id}/analyze",
        headers=auth_headers(auth),
    )
    second = client.post(
        f"/api/sentiment/instagram/accounts/{account_id}/analyze",
        headers=auth_headers(auth),
    )

    assert first.status_code == 200
    assert first.json() == {"analyzed_comments": 3}
    assert second.status_code == 200

    sentiments = list(db.scalars(select(CommentSentiment)))
    assert len(sentiments) == 3
    assert {item.label for item in sentiments} == {"positive", "neutral", "negative"}


def test_account_summary_returns_percentages(client, db) -> None:
    auth, account_id, _ = seed_account_with_comments(client, db)

    analyze = client.post(
        f"/api/sentiment/instagram/accounts/{account_id}/analyze",
        headers=auth_headers(auth),
    )
    assert analyze.status_code == 200

    response = client.get(
        f"/api/sentiment/instagram/accounts/{account_id}",
        headers=auth_headers(auth),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["positive"] == 1
    assert body["neutral"] == 1
    assert body["negative"] == 1
    assert body["positive_percentage"] == 33.33
    assert body["neutral_percentage"] == 33.33
    assert body["negative_percentage"] == 33.33


def test_media_summary_returns_post_sentiment(client, db) -> None:
    auth, account_id, media_id = seed_account_with_comments(client, db)

    analyze = client.post(
        f"/api/sentiment/instagram/accounts/{account_id}/analyze",
        headers=auth_headers(auth),
    )
    assert analyze.status_code == 200

    response = client.get(
        f"/api/sentiment/instagram/accounts/{account_id}/media/{media_id}",
        headers=auth_headers(auth),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 3


def test_empty_account_summary_returns_zeroes(client, db) -> None:
    auth = signup(client)
    user = UserRepository(db).get_by_email(EMAIL)
    assert user is not None

    account = InstagramAccount(
        user_id=user.id,
        instagram_user_id="ig-empty",
        username="empty",
        access_token_encrypted=encrypt_instagram_token("fake-access-token"),
        token_expires_at=None,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    response = client.get(
        f"/api/sentiment/instagram/accounts/{account.id}",
        headers=auth_headers(auth),
    )

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "positive_percentage": 0.0,
        "neutral_percentage": 0.0,
        "negative_percentage": 0.0,
    }


def test_sentiment_is_scoped_to_account_owner(client, db) -> None:
    first_auth, account_id, _ = seed_account_with_comments(client, db)

    second = client.post(
        "/api/auth/signup",
        json={"email": "second@example.com", "password": PASSWORD},
    )
    assert second.status_code == 201

    response = client.get(
        f"/api/sentiment/instagram/accounts/{account_id}",
        headers=auth_headers(second.json()),
    )

    assert response.status_code == 404
    assert first_auth["user"]["email"] == EMAIL
