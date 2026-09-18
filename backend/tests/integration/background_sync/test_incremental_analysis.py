from veya.application.safety.provider import SafetyClassification
from veya.application.safety.service import SafetyService
from veya.application.sentiment.provider import SentimentClassification
from veya.application.sentiment.service import SentimentService
from veya.domain.instagram.models import InstagramAccount, InstagramComment, InstagramMedia
from veya.domain.safety.models import CommentSafety
from veya.domain.sentiment.models import CommentSentiment
from veya.infrastructure.instagram.token_cipher import encrypt_instagram_token
from veya.repositories.users import UserRepository


EMAIL = "incremental@example.com"
PASSWORD = "strong-password-123"


class FakeSentimentProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def classify(self, text: str) -> SentimentClassification:
        self.calls.append(text)
        return SentimentClassification(
            label="positive",
            confidence=0.9,
            positive_score=0.9,
            neutral_score=0.1,
            negative_score=0.0,
            compound_score=0.8,
            provider="fake",
        )


class FakeSafetyProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def classify(self, text: str) -> SafetyClassification:
        self.calls.append(text)
        return SafetyClassification(
            primary_label="safe",
            constructive_score=0.0,
            toxic_score=0.0,
            severe_abuse_score=0.0,
            spam_score=0.0,
            should_shield=False,
            provider="fake",
        )


def seed_comments(client, db):
    signup = client.post(
        "/api/auth/signup",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert signup.status_code == 201

    user = UserRepository(db).get_by_email(EMAIL)
    assert user is not None

    account = InstagramAccount(
        user_id=user.id,
        instagram_user_id="ig-incremental",
        username="creator",
        access_token_encrypted=encrypt_instagram_token("fake-access-token"),
        token_expires_at=None,
    )
    db.add(account)
    db.flush()

    media = InstagramMedia(
        instagram_account_id=account.id,
        instagram_media_id="media-incremental",
        media_type="REELS",
        caption="Test",
    )
    db.add(media)
    db.flush()

    old = InstagramComment(
        instagram_media_id=media.id,
        instagram_comment_id="old-comment",
        text="Already analyzed",
        username="old",
    )
    new = InstagramComment(
        instagram_media_id=media.id,
        instagram_comment_id="new-comment",
        text="New comment",
        username="new",
    )
    db.add_all([old, new])
    db.flush()

    db.add(
        CommentSentiment(
            instagram_comment_id=old.id,
            label="neutral",
            confidence=1.0,
            positive_score=0.0,
            neutral_score=1.0,
            negative_score=0.0,
            compound_score=0.0,
            provider="seed",
        )
    )
    db.add(
        CommentSafety(
            instagram_comment_id=old.id,
            primary_label="safe",
            constructive_score=0.0,
            toxic_score=0.0,
            severe_abuse_score=0.0,
            spam_score=0.0,
            should_shield=False,
            provider="seed",
        )
    )
    db.commit()
    return user, account


def test_pending_analysis_only_processes_missing_comments(client, db) -> None:
    user, account = seed_comments(client, db)
    sentiment_provider = FakeSentimentProvider()
    safety_provider = FakeSafetyProvider()

    sentiment = SentimentService(db, provider=sentiment_provider).analyze_pending_account(
        user=user,
        account_id=account.id,
    )
    safety = SafetyService(db, provider=safety_provider).analyze_pending_account(
        user=user,
        account_id=account.id,
    )

    assert sentiment.analyzed_comments == 1
    assert safety.analyzed_comments == 1
    assert sentiment_provider.calls == ["New comment"]
    assert safety_provider.calls == ["New comment"]
