from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from veya.domain.instagram.models import InstagramComment


class InstagramCommentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_media_id(self, instagram_media_id: int) -> list[InstagramComment]:
        return list(
            self.db.scalars(
                select(InstagramComment)
                .where(InstagramComment.instagram_media_id == instagram_media_id)
                .order_by(
                    InstagramComment.commented_at.asc().nullslast(),
                    InstagramComment.id.asc(),
                )
            )
        )

    def get_by_external_id(
        self,
        *,
        instagram_media_id: int,
        instagram_comment_id: str,
    ) -> InstagramComment | None:
        return self.db.scalar(
            select(InstagramComment).where(
                InstagramComment.instagram_media_id == instagram_media_id,
                InstagramComment.instagram_comment_id == instagram_comment_id,
            )
        )

    def upsert(
        self,
        *,
        instagram_media_id: int,
        instagram_comment_id: str,
        text: str,
        username: str | None,
        commented_at,
    ) -> InstagramComment:
        comment = self.get_by_external_id(
            instagram_media_id=instagram_media_id,
            instagram_comment_id=instagram_comment_id,
        )

        if comment is None:
            comment = InstagramComment(
                instagram_media_id=instagram_media_id,
                instagram_comment_id=instagram_comment_id,
            )
            self.db.add(comment)

        comment.text = text
        comment.username = username
        comment.commented_at = commented_at
        comment.last_synced_at = datetime.now(timezone.utc)
        self.db.flush()
        return comment
