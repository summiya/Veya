from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from veya.application.insights.provider import AudienceInsightsResult
from veya.domain.insights.models import AudienceInsight


class AudienceInsightRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_account_id(self, instagram_account_id: int) -> AudienceInsight | None:
        return self.db.scalar(
            select(AudienceInsight).where(
                AudienceInsight.instagram_account_id == instagram_account_id
            )
        )

    def upsert(
        self,
        *,
        instagram_account_id: int,
        source_comment_count: int,
        result: AudienceInsightsResult,
    ) -> AudienceInsight:
        insight = self.get_by_account_id(instagram_account_id)

        if insight is None:
            insight = AudienceInsight(instagram_account_id=instagram_account_id)
            self.db.add(insight)

        insight.summary = result.summary
        insight.what_people_loved = result.what_people_loved
        insight.constructive_feedback = result.constructive_feedback
        insight.recurring_complaints = result.recurring_complaints
        insight.common_questions = result.common_questions
        insight.content_suggestions = result.content_suggestions
        insight.provider = result.provider
        insight.model = result.model
        insight.source_comment_count = source_comment_count
        insight.generated_at = datetime.now(timezone.utc)

        self.db.flush()
        return insight
