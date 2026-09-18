from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from veya.application.safety.provider import SafetyProvider
from veya.domain.instagram.models import InstagramAccount, InstagramComment, InstagramMedia
from veya.domain.safety.models import CommentSafety
from veya.domain.users.models import User
from veya.infrastructure.safety.heuristic import HeuristicSafetyProvider
from veya.repositories.comment_safety import CommentSafetyRepository
from veya.repositories.instagram_accounts import InstagramAccountRepository


class SafetyAnalysisError(RuntimeError):
    pass


@dataclass(frozen=True)
class SafetyAnalyzeResult:
    analyzed_comments: int


@dataclass(frozen=True)
class SafetySummary:
    total: int
    safe: int
    constructive: int
    toxic: int
    severe_abuse: int
    spam: int
    shielded: int


class SafetyService:
    def __init__(
        self,
        db: Session,
        provider: SafetyProvider | None = None,
    ) -> None:
        self.db = db
        self.provider = provider or HeuristicSafetyProvider()
        self.safety = CommentSafetyRepository(db)
        self.accounts = InstagramAccountRepository(db)

    def analyze_account(self, *, user: User, account_id: int) -> SafetyAnalyzeResult:
        account = self._get_owned_account(user=user, account_id=account_id)
        comments = list(
            self.db.scalars(
                select(InstagramComment)
                .join(InstagramMedia)
                .where(InstagramMedia.instagram_account_id == account.id)
                .order_by(InstagramComment.id.asc())
            )
        )

        for comment in comments:
            classification = self.provider.classify(comment.text)
            self.safety.upsert(
                instagram_comment_id=comment.id,
                classification=classification,
            )

        self.db.commit()
        return SafetyAnalyzeResult(analyzed_comments=len(comments))

    def analyze_pending_account(
        self,
        *,
        user: User,
        account_id: int,
    ) -> SafetyAnalyzeResult:
        account = self._get_owned_account(user=user, account_id=account_id)

        comments = list(
            self.db.scalars(
                select(InstagramComment)
                .join(InstagramMedia)
                .outerjoin(
                    CommentSafety,
                    CommentSafety.instagram_comment_id == InstagramComment.id,
                )
                .where(
                    InstagramMedia.instagram_account_id == account.id,
                    CommentSafety.id.is_(None),
                )
                .order_by(InstagramComment.id.asc())
            )
        )

        for comment in comments:
            classification = self.provider.classify(comment.text)
            self.safety.upsert(
                instagram_comment_id=comment.id,
                classification=classification,
            )

        self.db.commit()
        return SafetyAnalyzeResult(analyzed_comments=len(comments))

    def account_summary(self, *, user: User, account_id: int) -> SafetySummary:
        account = self._get_owned_account(user=user, account_id=account_id)

        rows = self.db.execute(
            select(CommentSafety.primary_label, func.count(CommentSafety.id))
            .join(
                InstagramComment,
                InstagramComment.id == CommentSafety.instagram_comment_id,
            )
            .join(
                InstagramMedia,
                InstagramMedia.id == InstagramComment.instagram_media_id,
            )
            .where(InstagramMedia.instagram_account_id == account.id)
            .group_by(CommentSafety.primary_label)
        ).all()

        shielded = self.db.scalar(
            select(func.count(CommentSafety.id))
            .join(
                InstagramComment,
                InstagramComment.id == CommentSafety.instagram_comment_id,
            )
            .join(
                InstagramMedia,
                InstagramMedia.id == InstagramComment.instagram_media_id,
            )
            .where(
                InstagramMedia.instagram_account_id == account.id,
                CommentSafety.should_shield.is_(True),
            )
        ) or 0

        counts = {
            "safe": 0,
            "constructive": 0,
            "toxic": 0,
            "severe_abuse": 0,
            "spam": 0,
        }
        for label, count in rows:
            if label in counts:
                counts[label] = int(count)

        return SafetySummary(
            total=sum(counts.values()),
            safe=counts["safe"],
            constructive=counts["constructive"],
            toxic=counts["toxic"],
            severe_abuse=counts["severe_abuse"],
            spam=counts["spam"],
            shielded=int(shielded),
        )

    def positive_and_constructive_comments(
        self,
        *,
        user: User,
        account_id: int,
        limit: int = 50,
    ) -> list[InstagramComment]:
        account = self._get_owned_account(user=user, account_id=account_id)

        return list(
            self.db.scalars(
                select(InstagramComment)
                .join(InstagramMedia)
                .join(
                    CommentSafety,
                    CommentSafety.instagram_comment_id == InstagramComment.id,
                )
                .where(
                    InstagramMedia.instagram_account_id == account.id,
                    CommentSafety.primary_label.in_(["safe", "constructive"]),
                    CommentSafety.should_shield.is_(False),
                )
                .order_by(InstagramComment.commented_at.desc().nullslast())
                .limit(limit)
            )
        )

    def shielded_comments(
        self,
        *,
        user: User,
        account_id: int,
        reveal: bool,
        limit: int = 50,
    ) -> list[InstagramComment]:
        account = self._get_owned_account(user=user, account_id=account_id)
        if not reveal:
            return []

        return list(
            self.db.scalars(
                select(InstagramComment)
                .join(InstagramMedia)
                .join(
                    CommentSafety,
                    CommentSafety.instagram_comment_id == InstagramComment.id,
                )
                .where(
                    InstagramMedia.instagram_account_id == account.id,
                    CommentSafety.should_shield.is_(True),
                )
                .order_by(InstagramComment.commented_at.desc().nullslast())
                .limit(limit)
            )
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
            raise SafetyAnalysisError("Instagram account not found")
        return account
