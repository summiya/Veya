from sqlalchemy import select

from veya.application.insights.provider import AudienceInsightsResult
from veya.application.insights.service import AudienceInsightsService
from veya.domain.insights.models import AudienceInsight
from veya.domain.instagram.models import InstagramAccount, InstagramComment, InstagramMedia
from veya.domain.safety.models import CommentSafety
from veya.domain.sentiment.models import CommentSentiment
from veya.infrastructure.instagram.token_cipher import encrypt_instagram_token
from veya.repositories.users import UserRepository


EMAIL = "creator@example.com"
PASSWORD = "strong-password-123"


class FakeInsightsProvider:
    def __init__(self) -> None:
        self.comments = []

    def generate(self, comments):
        self.comments = comments
        return AudienceInsightsResult(
            summary="People like the editing and want clearer audio.",
            what_people_loved=["Editing"],
            constructive_feedback=["Increase audio volume"],
            recurring_complaints=["Audio is low"],
            common_questions=["Where is the location?"],
            content_suggestions=["Add location details"],
            provider="fake",
            model="fake-model",
        )


def signup(client) -> dict:
    response = client.post(
        "/api/auth/signup",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()


def seed_insight_data(client, db):
    auth = signup(client)
    user = UserRepository(db).get_by_email(EMAIL)
    assert user is not None

    account = InstagramAccount(
        user_id=user.id,
        instagram_user_id="ig-insights",
        username="creator",
        access_token_encrypted=encrypt_instagram_token("fake-access-token"),
        token_expires_at=None,
    )
    db.add(account)
    db.flush()

    media = InstagramMedia(
        instagram_account_id=account.id,
        instagram_media_id="media-insights",
        media_type="REELS",
        caption="Travel reel",
    )
    db.add(media)
    db.flush()

    safe = InstagramComment(
        instagram_media_id=media.id,
        instagram_comment_id="safe-1",
        text="Love the editing!",
        username="fan",
    )
    constructive = InstagramComment(
        instagram_media_id=media.id,
        instagram_comment_id="constructive-1",
        text="The audio is low, please increase the volume.",
        username="helpful",
    )
    shielded = InstagramComment(
        instagram_media_id=media.id,
        instagram_comment_id="shielded-1",
        text="You are an idiot.",
        username="toxic",
    )
    spam = InstagramComment(
        instagram_media_id=media.id,
        instagram_comment_id="spam-1",
        text="DM me for promotion.",
        username="spam",
    )
    db.add_all([safe, constructive, shielded, spam])
    db.flush()

    db.add_all(
        [
            CommentSentiment(
                instagram_comment_id=safe.id,
                label="positive",
                confidence=0.9,
                positive_score=0.9,
                neutral_score=0.1,
                negative_score=0.0,
                compound_score=0.8,
                provider="test",
            ),
            CommentSentiment(
                instagram_comment_id=constructive.id,
                label="negative",
                confidence=0.7,
                positive_score=0.0,
                neutral_score=0.3,
                negative_score=0.7,
                compound_score=-0.4,
                provider="test",
            ),
        ]
    )
    db.add_all(
        [
            CommentSafety(
                instagram_comment_id=safe.id,
                primary_label="safe",
                constructive_score=0,
                toxic_score=0,
                severe_abuse_score=0,
                spam_score=0,
                should_shield=False,
                provider="test",
            ),
            CommentSafety(
                instagram_comment_id=constructive.id,
                primary_label="constructive",
                constructive_score=0.8,
                toxic_score=0,
                severe_abuse_score=0,
                spam_score=0,
                should_shield=False,
                provider="test",
            ),
            CommentSafety(
                instagram_comment_id=shielded.id,
                primary_label="toxic",
                constructive_score=0,
                toxic_score=0.9,
                severe_abuse_score=0,
                spam_score=0,
                should_shield=True,
                provider="test",
            ),
            CommentSafety(
                instagram_comment_id=spam.id,
                primary_label="spam",
                constructive_score=0,
                toxic_score=0,
                severe_abuse_score=0,
                spam_score=0.9,
                should_shield=False,
                provider="test",
            ),
        ]
    )
    db.commit()
    return auth, user, account


def test_generation_only_sends_safe_and_constructive_comments(client, db) -> None:
    _, user, account = seed_insight_data(client, db)
    provider = FakeInsightsProvider()

    insight = AudienceInsightsService(db, provider=provider).generate(
        user=user,
        account_id=account.id,
    )

    assert insight.source_comment_count == 2
    assert {item.safety_label for item in provider.comments} == {"safe", "constructive"}
    assert {item.text for item in provider.comments} == {
        "Love the editing!",
        "The audio is low, please increase the volume.",
    }


def test_regeneration_updates_single_snapshot(client, db) -> None:
    _, user, account = seed_insight_data(client, db)
    provider = FakeInsightsProvider()
    service = AudienceInsightsService(db, provider=provider)

    first = service.generate(user=user, account_id=account.id)
    second = service.generate(user=user, account_id=account.id)

    assert first.id == second.id
    assert len(list(db.scalars(select(AudienceInsight)))) == 1


def test_get_endpoint_returns_null_before_generation(client, db) -> None:
    auth, _, account = seed_insight_data(client, db)

    response = client.get(
        f"/api/insights/instagram/accounts/{account.id}",
        headers={"Authorization": f"Bearer {auth['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json() is None


def test_empty_safe_comment_set_skips_llm(client, db) -> None:
    auth = signup(client)
    user = UserRepository(db).get_by_email(EMAIL)
    assert user is not None

    account = InstagramAccount(
        user_id=user.id,
        instagram_user_id="ig-empty-insights",
        username="creator",
        access_token_encrypted=encrypt_instagram_token("fake-access-token"),
        token_expires_at=None,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    provider = FakeInsightsProvider()
    insight = AudienceInsightsService(db, provider=provider).generate(
        user=user,
        account_id=account.id,
    )

    assert insight.source_comment_count == 0
    assert provider.comments == []
    assert insight.provider == "system"
