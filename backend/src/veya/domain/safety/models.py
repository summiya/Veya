from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veya.infrastructure.database.session import Base


class CommentSafety(Base):
    __tablename__ = "comment_safety"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instagram_comment_id: Mapped[int] = mapped_column(
        ForeignKey("instagram_comments.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    primary_label: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    constructive_score: Mapped[float] = mapped_column(Float, nullable=False)
    toxic_score: Mapped[float] = mapped_column(Float, nullable=False)
    severe_abuse_score: Mapped[float] = mapped_column(Float, nullable=False)
    spam_score: Mapped[float] = mapped_column(Float, nullable=False)
    should_shield: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    comment = relationship("InstagramComment", back_populates="safety")
