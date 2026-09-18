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


@dataclass(frozen=True)
class InstagramMediaItem:
    media_id: str
    media_type: str
    caption: str | None
    media_url: str | None
    thumbnail_url: str | None
    permalink: str | None
    timestamp: datetime | None


@dataclass(frozen=True)
class InstagramCommentItem:
    comment_id: str
    text: str
    username: str | None
    timestamp: datetime | None


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

    def list_media(self, *, access_token: str, instagram_user_id: str) -> list[InstagramMediaItem]:
        url = f"{settings.instagram_graph_url}/{instagram_user_id}/media"
        params: dict[str, str] | None = {
            "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp",
            "access_token": access_token,
        }
        items: list[InstagramMediaItem] = []

        while url:
            body = self._get_json(url, params=params, error_message="Instagram media request failed")
            params = None

            for raw in body.get("data", []):
                items.append(
                    InstagramMediaItem(
                        media_id=str(raw["id"]),
                        media_type=str(raw.get("media_type", "UNKNOWN")),
                        caption=raw.get("caption"),
                        media_url=raw.get("media_url"),
                        thumbnail_url=raw.get("thumbnail_url"),
                        permalink=raw.get("permalink"),
                        timestamp=self._parse_timestamp(raw.get("timestamp")),
                    )
                )

            url = body.get("paging", {}).get("next")

        return items

    def list_comments(
        self,
        *,
        access_token: str,
        instagram_media_id: str,
    ) -> list[InstagramCommentItem]:
        url = f"{settings.instagram_graph_url}/{instagram_media_id}/comments"
        params: dict[str, str] | None = {
            "fields": "id,text,username,timestamp",
            "access_token": access_token,
        }
        items: list[InstagramCommentItem] = []

        while url:
            body = self._get_json(url, params=params, error_message="Instagram comments request failed")
            params = None

            for raw in body.get("data", []):
                items.append(
                    InstagramCommentItem(
                        comment_id=str(raw["id"]),
                        text=str(raw.get("text", "")),
                        username=raw.get("username"),
                        timestamp=self._parse_timestamp(raw.get("timestamp")),
                    )
                )

            url = body.get("paging", {}).get("next")

        return items

    def _get_json(
        self,
        url: str,
        *,
        params: dict[str, str] | None,
        error_message: str,
    ) -> dict:
        try:
            response = self.http.get(url, params=params)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise InstagramApiError(error_message) from exc

        if not isinstance(body, dict):
            raise InstagramApiError(error_message)
        return body

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
