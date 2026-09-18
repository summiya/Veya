from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from veya.application.sentiment.provider import SentimentProvider
from veya.domain.instagram.models import InstagramAccount, InstagramComment, InstagramMedia
from veya.domain.sentiment.models import CommentSentiment
from veya.domain.users.models import User
from veya.infrastructure.sentiment.vader import VaderSentimentProvider
from veya.repositories.comment_sentiments import CommentSentimentRepository
from veya.repositories.instagram_accounts import InstagramAccountRepository


class SentimentAnalysisError(RuntimeError):
    pass


@dataclass(frozen=True)
class SentimentBreakdown:
    total: int
    positive: int
    neutral: int
    negative: int
    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float


@dataclass(frozen=True)
class AnalyzeSentimentResult:
    analyzed_comments: int


class SentimentService:
    def __init__(
        self,
        db: Session,
        provider: SentimentProvider | None = None,
    ) -> None:
        self.db = db
        self.provider = provider or VaderSentimentProvider()
        self.sentiments = CommentSentimentRepository(db)
        self.accounts = InstagramAccountRepository(db)

    def analyze_account(self, *, user: User, account_id: int) -> AnalyzeSentimentResult:
        account = self._get_owned_account(user=user, account_id=account_id)

        comments = list(
            self.db.scalars(
                select(InstagramComment)
                .join(InstagramMedia)
                .where(InstagramMedia.instagram_account_id == account.id)
                .order_by(InstagramComment.id.asc())
            )
        )

        analyzed = 0
        for comment in comments:
            classification = self.provider.classify(comment.text)
            self.sentiments.upsert(
                instagram_comment_id=comment.id,
                classification=classification,
            )
            analyzed += 1

        self.db.commit()
        return AnalyzeSentimentResult(analyzed_comments=analyzed)

    def analyze_pending_account(
        self,
        *,
        user: User,
        account_id: int,
    ) -> AnalyzeSentimentResult:
        account = self._get_owned_account(user=user, account_id=account_id)

        comments = list(
            self.db.scalars(
                select(InstagramComment)
                .join(InstagramMedia)
                .outerjoin(
                    CommentSentiment,
                    CommentSentiment.instagram_comment_id == InstagramComment.id,
                )
                .where(
                    InstagramMedia.instagram_account_id == account.id,
                    CommentSentiment.id.is_(None),
                )
                .order_by(InstagramComment.id.asc())
            )
        )

        for comment in comments:
            classification = self.provider.classify(comment.text)
            self.sentiments.upsert(
                instagram_comment_id=comment.id,
                classification=classification,
            )

        self.db.commit()
        return AnalyzeSentimentResult(analyzed_comments=len(comments))

    def account_summary(self, *, user: User, account_id: int) -> SentimentBreakdown:
        account = self._get_owned_account(user=user, account_id=account_id)
        return self._summary_for_account(account.id)

    def media_summary(
        self,
        *,
        user: User,
        account_id: int,
        media_id: int,
    ) -> SentimentBreakdown:
        account = self._get_owned_account(user=user, account_id=account_id)

        media = self.db.scalar(
            select(InstagramMedia).where(
                InstagramMedia.id == media_id,
                InstagramMedia.instagram_account_id == account.id,
            )
        )
        if media is None:
            raise SentimentAnalysisError("Instagram media not found")

        rows = self.db.execute(
            select(CommentSentiment.label, func.count(CommentSentiment.id))
            .join(
                InstagramComment,
                InstagramComment.id == CommentSentiment.instagram_comment_id,
            )
            .where(InstagramComment.instagram_media_id == media.id)
            .group_by(CommentSentiment.label)
        ).all()

        return self._to_breakdown(rows)

    def _summary_for_account(self, instagram_account_id: int) -> SentimentBreakdown:
        rows = self.db.execute(
            select(CommentSentiment.label, func.count(CommentSentiment.id))
            .join(
                InstagramComment,
                InstagramComment.id == CommentSentiment.instagram_comment_id,
            )
            .join(
                InstagramMedia,
                InstagramMedia.id == InstagramComment.instagram_media_id,
            )
            .where(InstagramMedia.instagram_account_id == instagram_account_id)
            .group_by(CommentSentiment.label)
        ).all()

        return self._to_breakdown(rows)

    @staticmethod
    def _to_breakdown(rows) -> SentimentBreakdown:
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        for label, count in rows:
            if label in counts:
                counts[label] = int(count)

        total = sum(counts.values())

        def percentage(value: int) -> float:
            if total == 0:
                return 0.0
            return round((value / total) * 100, 2)

        return SentimentBreakdown(
            total=total,
            positive=counts["positive"],
            neutral=counts["neutral"],
            negative=counts["negative"],
            positive_percentage=percentage(counts["positive"]),
            neutral_percentage=percentage(counts["neutral"]),
            negative_percentage=percentage(counts["negative"]),
        )

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
            raise SentimentAnalysisError("Instagram account not found")
        return account
