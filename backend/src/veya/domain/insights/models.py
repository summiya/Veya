from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veya.infrastructure.database.session import Base


class AudienceInsight(Base):
    __tablename__ = "audience_insights"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instagram_account_id: Mapped[int] = mapped_column(
        ForeignKey("instagram_accounts.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    what_people_loved: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    constructive_feedback: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    recurring_complaints: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    common_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    content_suggestions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    source_comment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    account = relationship("InstagramAccount", back_populates="audience_insight")
