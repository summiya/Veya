from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InstagramSyncResponse(BaseModel):
    media_count: int
    comment_count: int


class InstagramMediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instagram_media_id: str
    media_type: str
    caption: str | None
    media_url: str | None
    thumbnail_url: str | None
    permalink: str | None
    posted_at: datetime | None
    last_synced_at: datetime


class InstagramCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instagram_comment_id: str
    text: str
    username: str | None
    commented_at: datetime | None
    last_synced_at: datetime
