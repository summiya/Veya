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
    created_at: datetime


class InstagramCallbackResponse(BaseModel):
    account: InstagramAccountResponse
