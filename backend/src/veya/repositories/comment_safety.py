from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from veya.application.safety.provider import SafetyClassification
from veya.domain.safety.models import CommentSafety


class CommentSafetyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_comment_id(self, instagram_comment_id: int) -> CommentSafety | None:
        return self.db.scalar(
            select(CommentSafety).where(
                CommentSafety.instagram_comment_id == instagram_comment_id
            )
        )

    def upsert(
        self,
        *,
        instagram_comment_id: int,
        classification: SafetyClassification,
    ) -> CommentSafety:
        safety = self.get_by_comment_id(instagram_comment_id)

        if safety is None:
            safety = CommentSafety(instagram_comment_id=instagram_comment_id)
            self.db.add(safety)

        safety.primary_label = classification.primary_label
        safety.constructive_score = classification.constructive_score
        safety.toxic_score = classification.toxic_score
        safety.severe_abuse_score = classification.severe_abuse_score
        safety.spam_score = classification.spam_score
        safety.should_shield = classification.should_shield
        safety.provider = classification.provider
        safety.analyzed_at = datetime.now(timezone.utc)
        self.db.flush()
        return safety
