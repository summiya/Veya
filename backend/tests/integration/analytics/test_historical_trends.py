from sqlalchemy import select

from veya.domain.analytics.models import AudienceHealthSnapshot
from veya.domain.instagram.models import InstagramAccount, InstagramComment, InstagramMedia
from veya.domain.safety.models import CommentSafety
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


def seed_account(client, db):
    auth = signup(client)
    user = UserRepository(db).get_by_email(EMAIL)
    assert user is not None

    account = InstagramAccount(
        user_id=user.id,
        instagram_user_id="ig-trends",
        username="creator",
        access_token_encrypted=encrypt_instagram_token("fake-access-token"),
        token_expires_at=None,
    )
    db.add(account)
    db.flush()

    media = InstagramMedia(
        instagram_account_id=account.id,
        instagram_media_id="media-trends",
        media_type="REELS",
        caption="Trend test",
    )
    db.add(media)
    db.flush()

    comments = [
        InstagramComment(
            instagram_media_id=media.id,
            instagram_comment_id=f"comment-{index}",
            text=f"Comment {index}",
            username=f"user{index}",
        )
        for index in range(1, 5)
    ]
    db.add_all(comments)
    db.flush()

    sentiment_labels = ["positive", "positive", "neutral", "negative"]
    safety_labels = ["safe", "constructive", "safe", "toxic"]

    for index, comment in enumerate(comments):
        label = sentiment_labels[index]
        db.add(
            CommentSentiment(
                instagram_comment_id=comment.id,
                label=label,
                confidence=0.9,
                positive_score=1.0 if label == "positive" else 0.0,
                neutral_score=1.0 if label == "neutral" else 0.0,
                negative_score=1.0 if label == "negative" else 0.0,
                compound_score=0.8 if label == "positive" else (-0.8 if label == "negative" else 0.0),
                provider="test",
            )
        )

        safety_label = safety_labels[index]
        db.add(
            CommentSafety(
                instagram_comment_id=comment.id,
                primary_label=safety_label,
                constructive_score=0.8 if safety_label == "constructive" else 0.0,
                toxic_score=0.9 if safety_label == "toxic" else 0.0,
                severe_abuse_score=0.0,
                spam_score=0.0,
                should_shield=safety_label == "toxic",
                provider="test",
            )
        )

    db.commit()
    return auth, account, comments


def test_capture_snapshot_records_current_health(client, db) -> None:
    auth, account, _ = seed_account(client, db)

    response = client.post(
        f"/api/analytics/instagram/accounts/{account.id}/snapshots",
        headers=auth_headers(auth),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["analyzed_comment_count"] == 4
    assert body["positive_percentage"] == 50.0
    assert body["neutral_percentage"] == 25.0
    assert body["negative_percentage"] == 25.0
    assert body["constructive"] == 1
    assert body["toxic"] == 1
    assert body["shielded"] == 1


def test_trend_reports_change_between_snapshots(client, db) -> None:
    auth, account, comments = seed_account(client, db)

    first = client.post(
        f"/api/analytics/instagram/accounts/{account.id}/snapshots",
        headers=auth_headers(auth),
    )
    assert first.status_code == 201

    negative_sentiment = db.scalar(
        select(CommentSentiment).where(
            CommentSentiment.instagram_comment_id == comments[3].id
        )
    )
    assert negative_sentiment is not None
    negative_sentiment.label = "positive"
    negative_sentiment.positive_score = 1.0
    negative_sentiment.negative_score = 0.0
    negative_sentiment.compound_score = 0.9

    toxic_safety = db.scalar(
        select(CommentSafety).where(
            CommentSafety.instagram_comment_id == comments[3].id
        )
    )
    assert toxic_safety is not None
    toxic_safety.primary_label = "safe"
    toxic_safety.toxic_score = 0.0
    toxic_safety.should_shield = False
    db.commit()

    second = client.post(
        f"/api/analytics/instagram/accounts/{account.id}/snapshots",
        headers=auth_headers(auth),
    )
    assert second.status_code == 201

    trend = client.get(
        f"/api/analytics/instagram/accounts/{account.id}/trends?days=30",
        headers=auth_headers(auth),
    )

    assert trend.status_code == 200
    body = trend.json()
    assert len(body["points"]) == 2
    assert body["positive_change"] == 25.0
    assert body["negative_change"] == -25.0
    assert body["shielded_change"] == -1


def test_one_snapshot_has_no_change_baseline(client, db) -> None:
    auth, account, _ = seed_account(client, db)

    capture = client.post(
        f"/api/analytics/instagram/accounts/{account.id}/snapshots",
        headers=auth_headers(auth),
    )
    assert capture.status_code == 201

    trend = client.get(
        f"/api/analytics/instagram/accounts/{account.id}/trends?days=30",
        headers=auth_headers(auth),
    )

    assert trend.status_code == 200
    assert trend.json()["positive_change"] is None
    assert trend.json()["negative_change"] is None
    assert trend.json()["shielded_change"] is None


def test_snapshot_history_is_scoped_to_account_owner(client, db) -> None:
    first_auth, account, _ = seed_account(client, db)

    capture = client.post(
        f"/api/analytics/instagram/accounts/{account.id}/snapshots",
        headers=auth_headers(first_auth),
    )
    assert capture.status_code == 201

    second = client.post(
        "/api/auth/signup",
        json={"email": "second@example.com", "password": PASSWORD},
    )
    assert second.status_code == 201

    response = client.get(
        f"/api/analytics/instagram/accounts/{account.id}/trends",
        headers=auth_headers(second.json()),
    )

    assert response.status_code == 404
    assert len(list(db.scalars(select(AudienceHealthSnapshot)))) == 1
