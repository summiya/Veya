from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from veya.domain.analytics.models import AudienceHealthSnapshot


class AudienceHealthSnapshotRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        instagram_account_id: int,
        analyzed_comment_count: int,
        positive: int,
        neutral: int,
        negative: int,
        positive_percentage: float,
        neutral_percentage: float,
        negative_percentage: float,
        constructive: int,
        toxic: int,
        severe_abuse: int,
        spam: int,
        shielded: int,
    ) -> AudienceHealthSnapshot:
        snapshot = AudienceHealthSnapshot(
            instagram_account_id=instagram_account_id,
            analyzed_comment_count=analyzed_comment_count,
            positive=positive,
            neutral=neutral,
            negative=negative,
            positive_percentage=positive_percentage,
            neutral_percentage=neutral_percentage,
            negative_percentage=negative_percentage,
            constructive=constructive,
            toxic=toxic,
            severe_abuse=severe_abuse,
            spam=spam,
            shielded=shielded,
        )
        self.db.add(snapshot)
        self.db.flush()
        return snapshot

    def list_since(
        self,
        *,
        instagram_account_id: int,
        since: datetime,
    ) -> list[AudienceHealthSnapshot]:
        return list(
            self.db.scalars(
                select(AudienceHealthSnapshot)
                .where(
                    AudienceHealthSnapshot.instagram_account_id == instagram_account_id,
                    AudienceHealthSnapshot.captured_at >= since,
                )
                .order_by(AudienceHealthSnapshot.captured_at.asc(), AudienceHealthSnapshot.id.asc())
            )
        )
