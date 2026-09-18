from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from veya.domain.instagram.models import InstagramMedia


class InstagramMediaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_account_id(self, instagram_account_id: int) -> list[InstagramMedia]:
        return list(
            self.db.scalars(
                select(InstagramMedia)
                .where(InstagramMedia.instagram_account_id == instagram_account_id)
                .order_by(InstagramMedia.posted_at.desc().nullslast(), InstagramMedia.id.desc())
            )
        )

    def get_by_external_id(
        self,
        *,
        instagram_account_id: int,
        instagram_media_id: str,
    ) -> InstagramMedia | None:
        return self.db.scalar(
            select(InstagramMedia).where(
                InstagramMedia.instagram_account_id == instagram_account_id,
                InstagramMedia.instagram_media_id == instagram_media_id,
            )
        )

    def upsert(
        self,
        *,
        instagram_account_id: int,
        instagram_media_id: str,
        media_type: str,
        caption: str | None,
        media_url: str | None,
        thumbnail_url: str | None,
        permalink: str | None,
        posted_at,
    ) -> InstagramMedia:
        media = self.get_by_external_id(
            instagram_account_id=instagram_account_id,
            instagram_media_id=instagram_media_id,
        )

        if media is None:
            media = InstagramMedia(
                instagram_account_id=instagram_account_id,
                instagram_media_id=instagram_media_id,
                media_type=media_type,
            )
            self.db.add(media)

        media.caption = caption
        media.media_url = media_url
        media.thumbnail_url = thumbnail_url
        media.permalink = permalink
        media.posted_at = posted_at
        media.last_synced_at = datetime.now(timezone.utc)
        self.db.flush()
        return media
