from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from veya.application.sentiment.provider import SentimentClassification
from veya.domain.sentiment.models import CommentSentiment


class CommentSentimentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_comment_id(self, instagram_comment_id: int) -> CommentSentiment | None:
        return self.db.scalar(
            select(CommentSentiment).where(
                CommentSentiment.instagram_comment_id == instagram_comment_id
            )
        )

    def upsert(
        self,
        *,
        instagram_comment_id: int,
        classification: SentimentClassification,
    ) -> CommentSentiment:
        sentiment = self.get_by_comment_id(instagram_comment_id)

        if sentiment is None:
            sentiment = CommentSentiment(instagram_comment_id=instagram_comment_id)
            self.db.add(sentiment)

        sentiment.label = classification.label
        sentiment.confidence = classification.confidence
        sentiment.positive_score = classification.positive_score
        sentiment.neutral_score = classification.neutral_score
        sentiment.negative_score = classification.negative_score
        sentiment.compound_score = classification.compound_score
        sentiment.provider = classification.provider
        sentiment.analyzed_at = datetime.now(timezone.utc)

        self.db.flush()
        return sentiment
