from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veya.infrastructure.database.session import Base


class InstagramAccount(Base):
    __tablename__ = "instagram_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "instagram_user_id", name="uq_instagram_account_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    instagram_user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    access_token_encrypted: Mapped[str] = mapped_column(String(2048), nullable=False)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    last_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    user = relationship("User", back_populates="instagram_accounts")
    media = relationship(
        "InstagramMedia",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    audience_insight = relationship(
        "AudienceInsight",
        back_populates="account",
        cascade="all, delete-orphan",
        uselist=False,
    )
    health_snapshots = relationship(
        "AudienceHealthSnapshot",
        back_populates="account",
        cascade="all, delete-orphan",
    )
    sync_jobs = relationship(
        "InstagramSyncJob",
        back_populates="account",
        cascade="all, delete-orphan",
    )


class InstagramMedia(Base):
    __tablename__ = "instagram_media"
    __table_args__ = (
        UniqueConstraint(
            "instagram_account_id",
            "instagram_media_id",
            name="uq_instagram_media_account",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instagram_account_id: Mapped[int] = mapped_column(
        ForeignKey("instagram_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    instagram_media_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    media_type: Mapped[str] = mapped_column(String(32), nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    permalink: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    account = relationship("InstagramAccount", back_populates="media")
    comments = relationship(
        "InstagramComment",
        back_populates="media",
        cascade="all, delete-orphan",
    )


class InstagramComment(Base):
    __tablename__ = "instagram_comments"
    __table_args__ = (
        UniqueConstraint(
            "instagram_media_id",
            "instagram_comment_id",
            name="uq_instagram_comment_media",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instagram_media_id: Mapped[int] = mapped_column(
        ForeignKey("instagram_media.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    instagram_comment_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    media = relationship("InstagramMedia", back_populates="comments")
    sentiment = relationship(
        "CommentSentiment",
        back_populates="comment",
        cascade="all, delete-orphan",
        uselist=False,
    )
    safety = relationship(
        "CommentSafety",
        back_populates="comment",
        cascade="all, delete-orphan",
        uselist=False,
    )
