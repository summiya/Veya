from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from veya.application.safety.service import SafetyService
from veya.application.sentiment.service import SentimentService
from veya.domain.analytics.models import AudienceHealthSnapshot
from veya.domain.instagram.models import InstagramAccount
from veya.domain.users.models import User
from veya.repositories.audience_health_snapshots import AudienceHealthSnapshotRepository
from veya.repositories.instagram_accounts import InstagramAccountRepository


class AnalyticsError(RuntimeError):
    pass


@dataclass(frozen=True)
class TrendSummary:
    points: list[AudienceHealthSnapshot]
    positive_change: float | None
    negative_change: float | None
    shielded_change: int | None


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.accounts = InstagramAccountRepository(db)
        self.snapshots = AudienceHealthSnapshotRepository(db)

    def capture_snapshot(
        self,
        *,
        user: User,
        account_id: int,
    ) -> AudienceHealthSnapshot:
        account = self._get_owned_account(user=user, account_id=account_id)

        sentiment = SentimentService(self.db).account_summary(
            user=user,
            account_id=account.id,
        )
        safety = SafetyService(self.db).account_summary(
            user=user,
            account_id=account.id,
        )

        snapshot = self.snapshots.create(
            instagram_account_id=account.id,
            analyzed_comment_count=sentiment.total,
            positive=sentiment.positive,
            neutral=sentiment.neutral,
            negative=sentiment.negative,
            positive_percentage=sentiment.positive_percentage,
            neutral_percentage=sentiment.neutral_percentage,
            negative_percentage=sentiment.negative_percentage,
            constructive=safety.constructive,
            toxic=safety.toxic,
            severe_abuse=safety.severe_abuse,
            spam=safety.spam,
            shielded=safety.shielded,
        )
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def trend(
        self,
        *,
        user: User,
        account_id: int,
        days: int,
    ) -> TrendSummary:
        account = self._get_owned_account(user=user, account_id=account_id)
        since = datetime.now(timezone.utc) - timedelta(days=days)

        points = self.snapshots.list_since(
            instagram_account_id=account.id,
            since=since,
        )

        if len(points) < 2:
            return TrendSummary(
                points=points,
                positive_change=None,
                negative_change=None,
                shielded_change=None,
            )

        first = points[0]
        latest = points[-1]
        return TrendSummary(
            points=points,
            positive_change=round(
                latest.positive_percentage - first.positive_percentage,
                2,
            ),
            negative_change=round(
                latest.negative_percentage - first.negative_percentage,
                2,
            ),
            shielded_change=latest.shielded - first.shielded,
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
            raise AnalyticsError("Instagram account not found")
        return account
