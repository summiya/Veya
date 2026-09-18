from sqlalchemy import select
from sqlalchemy.orm import Session

from veya.application.insights.provider import (
    AudienceInsightsProvider,
    AudienceInsightsResult,
    InsightComment,
)
from veya.core.config import settings
from veya.domain.instagram.models import InstagramAccount, InstagramComment, InstagramMedia
from veya.domain.safety.models import CommentSafety
from veya.domain.sentiment.models import CommentSentiment
from veya.domain.users.models import User
from veya.infrastructure.insights.openai import (
    AudienceInsightsProviderError,
    OpenAIAudienceInsightsProvider,
)
from veya.repositories.audience_insights import AudienceInsightRepository
from veya.repositories.instagram_accounts import InstagramAccountRepository


class AudienceInsightsError(RuntimeError):
    pass


class AudienceInsightsService:
    def __init__(
        self,
        db: Session,
        provider: AudienceInsightsProvider | None = None,
    ) -> None:
        self.db = db
        self.provider = provider or OpenAIAudienceInsightsProvider()
        self.insights = AudienceInsightRepository(db)
        self.accounts = InstagramAccountRepository(db)

    def generate(self, *, user: User, account_id: int):
        account = self._get_owned_account(user=user, account_id=account_id)

        rows = self.db.execute(
            select(
                InstagramComment.text,
                CommentSentiment.label,
                CommentSafety.primary_label,
            )
            .join(
                InstagramMedia,
                InstagramMedia.id == InstagramComment.instagram_media_id,
            )
            .join(
                CommentSafety,
                CommentSafety.instagram_comment_id == InstagramComment.id,
            )
            .outerjoin(
                CommentSentiment,
                CommentSentiment.instagram_comment_id == InstagramComment.id,
            )
            .where(
                InstagramMedia.instagram_account_id == account.id,
                CommentSafety.should_shield.is_(False),
                CommentSafety.primary_label != "spam",
            )
            .order_by(InstagramComment.commented_at.desc().nullslast())
            .limit(settings.insights_max_comments)
        ).all()

        comments = [
            InsightComment(
                text=text,
                sentiment_label=sentiment_label,
                safety_label=safety_label,
            )
            for text, sentiment_label, safety_label in rows
        ]

        if comments:
            try:
                result = self.provider.generate(comments)
            except AudienceInsightsProviderError as exc:
                raise AudienceInsightsError(str(exc)) from exc
        else:
            result = AudienceInsightsResult(
                summary=(
                    "There are no eligible safe or constructive comments available "
                    "for audience insights yet."
                ),
                what_people_loved=[],
                constructive_feedback=[],
                recurring_complaints=[],
                common_questions=[],
                content_suggestions=[],
                provider="system",
                model="none",
            )

        insight = self.insights.upsert(
            instagram_account_id=account.id,
            source_comment_count=len(comments),
            result=result,
        )
        self.db.commit()
        self.db.refresh(insight)
        return insight

    def get_current(self, *, user: User, account_id: int):
        account = self._get_owned_account(user=user, account_id=account_id)
        return self.insights.get_by_account_id(account.id)

    def _get_owned_account(self, *, user: User, account_id: int) -> InstagramAccount:
        account = next(
            (
                account
                for account in self.accounts.get_by_user_id(user.id)
                if account.id == account_id
            ),
            None,
        )
        if account is None:
            raise AudienceInsightsError("Instagram account not found")
        return account
