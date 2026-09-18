from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InstagramSyncJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    trigger: str
    attempt_count: int
    media_synced: int
    comments_synced: int
    sentiment_analyzed: int
    safety_analyzed: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
