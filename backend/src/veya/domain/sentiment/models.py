from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veya.infrastructure.database.session import Base


class CommentSentiment(Base):
    __tablename__ = "comment_sentiments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instagram_comment_id: Mapped[int] = mapped_column(
        ForeignKey("instagram_comments.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    positive_score: Mapped[float] = mapped_column(Float, nullable=False)
    neutral_score: Mapped[float] = mapped_column(Float, nullable=False)
    negative_score: Mapped[float] = mapped_column(Float, nullable=False)
    compound_score: Mapped[float] = mapped_column(Float, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    comment = relationship("InstagramComment", back_populates="sentiment")
