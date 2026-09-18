from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from veya.core.config import settings


class InstagramApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class InstagramTokenResult:
    access_token: str
    instagram_user_id: str
    expires_at: datetime | None


@dataclass(frozen=True)
class InstagramProfile:
    instagram_user_id: str
    username: str | None


class InstagramClient:
    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.http = http_client or httpx.Client(timeout=15.0)

    def build_authorization_url(self, *, state: str) -> str:
        query = urlencode(
            {
                "client_id": settings.instagram_client_id,
                "redirect_uri": settings.instagram_redirect_uri,
                "response_type": "code",
                "scope": settings.instagram_scopes,
                "state": state,
            }
        )
        return f"{settings.instagram_authorize_url}?{query}"

    def exchange_code(self, code: str) -> InstagramTokenResult:
        try:
            response = self.http.post(
                settings.instagram_token_url,
                data={
                    "client_id": settings.instagram_client_id,
                    "client_secret": settings.instagram_client_secret,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.instagram_redirect_uri,
                    "code": code,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise InstagramApiError("Instagram token exchange failed") from exc

        body = response.json()
        access_token = body.get("access_token")
        user_id = body.get("user_id")

        if not access_token or user_id is None:
            raise InstagramApiError("Instagram token response is incomplete")

        expires_in = body.get("expires_in")
        expires_at = None
        if isinstance(expires_in, int):
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        return InstagramTokenResult(
            access_token=str(access_token),
            instagram_user_id=str(user_id),
            expires_at=expires_at,
        )

    def get_profile(self, access_token: str, instagram_user_id: str) -> InstagramProfile:
        try:
            response = self.http.get(
                f"{settings.instagram_graph_url}/{instagram_user_id}",
                params={
                    "fields": "id,username",
                    "access_token": access_token,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise InstagramApiError("Instagram profile request failed") from exc

        body = response.json()
        return InstagramProfile(
            instagram_user_id=str(body.get("id", instagram_user_id)),
            username=body.get("username"),
        )
