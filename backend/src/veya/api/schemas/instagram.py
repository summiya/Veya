from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InstagramConnectResponse(BaseModel):
    authorization_url: str


class InstagramAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instagram_user_id: str
    username: str | None
    token_expires_at: datetime | None
    sync_status: str
    last_synced_at: datetime | None
    next_sync_at: datetime | None
    last_sync_error: str | None
    created_at: datetime


class InstagramCallbackResponse(BaseModel):
    account: InstagramAccountResponse
