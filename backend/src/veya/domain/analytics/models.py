from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veya.infrastructure.database.session import Base


class AudienceHealthSnapshot(Base):
    __tablename__ = "audience_health_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instagram_account_id: Mapped[int] = mapped_column(
        ForeignKey("instagram_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    analyzed_comment_count: Mapped[int] = mapped_column(Integer, nullable=False)

    positive: Mapped[int] = mapped_column(Integer, nullable=False)
    neutral: Mapped[int] = mapped_column(Integer, nullable=False)
    negative: Mapped[int] = mapped_column(Integer, nullable=False)

    positive_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    neutral_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    negative_percentage: Mapped[float] = mapped_column(Float, nullable=False)

    constructive: Mapped[int] = mapped_column(Integer, nullable=False)
    toxic: Mapped[int] = mapped_column(Integer, nullable=False)
    severe_abuse: Mapped[int] = mapped_column(Integer, nullable=False)
    spam: Mapped[int] = mapped_column(Integer, nullable=False)
    shielded: Mapped[int] = mapped_column(Integer, nullable=False)

    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    account = relationship("InstagramAccount", back_populates="health_snapshots")
