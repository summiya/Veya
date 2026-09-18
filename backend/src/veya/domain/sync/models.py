from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veya.infrastructure.database.session import Base


class InstagramSyncJob(Base):
    __tablename__ = "instagram_sync_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instagram_account_id: Mapped[int] = mapped_column(
        ForeignKey("instagram_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="queued")
    trigger: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    media_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sentiment_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    safety_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    account = relationship("InstagramAccount", back_populates="sync_jobs")
