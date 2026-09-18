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
    connection_status: str
    last_connection_check_at: datetime | None
    last_token_refreshed_at: datetime | None
    last_api_error_code: str | None
    last_api_error_message: str | None
    sync_status: str
    last_synced_at: datetime | None
    next_sync_at: datetime | None
    last_sync_error: str | None
    created_at: datetime


class InstagramConnectionCheckResponse(BaseModel):
    account: InstagramAccountResponse
    token_refreshed: bool


class InstagramReadinessResponse(BaseModel):
    configured: bool
    missing_settings: list[str]
    redirect_uri: str
    scopes: list[str]


class InstagramDisconnectResponse(BaseModel):
    message: str
