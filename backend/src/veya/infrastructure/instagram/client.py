from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from veya.core.config import settings


class InstagramApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        subcode: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.subcode = subcode
        self.trace_id = trace_id

    @property
    def requires_reconnect(self) -> bool:
        return self.code == "190" or self.status_code in {401, 403}

    @property
    def retryable(self) -> bool:
        return self.status_code in {429, 500, 502, 503, 504}


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
        if not settings.instagram_client_id:
            raise InstagramApiError("INSTAGRAM_CLIENT_ID is not configured")

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
        if not settings.instagram_client_id or not settings.instagram_client_secret:
            raise InstagramApiError("Instagram OAuth credentials are not configured")

        response = self._post_response(
            settings.instagram_token_url,
            data={
                "client_id": settings.instagram_client_id,
                "client_secret": settings.instagram_client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": settings.instagram_redirect_uri,
                "code": code,
            },
            error_message="Instagram token exchange failed",
        )
        body = self._parse_response(
            response,
            error_message="Instagram token exchange failed",
        )

        access_token = body.get("access_token")
        user_id = body.get("user_id")

        if not access_token or user_id is None:
            raise InstagramApiError("Instagram token response is incomplete")

        return InstagramTokenResult(
            access_token=str(access_token),
            instagram_user_id=str(user_id),
            expires_at=self._expires_at(body.get("expires_in")),
        )

    def exchange_long_lived_token(
        self,
        *,
        short_lived_token: str,
        instagram_user_id: str,
    ) -> InstagramTokenResult:
        if not settings.instagram_client_secret:
            raise InstagramApiError("INSTAGRAM_CLIENT_SECRET is not configured")

        response = self._get_response(
            settings.instagram_long_lived_token_url,
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": settings.instagram_client_secret,
                "access_token": short_lived_token,
            },
            error_message="Instagram long-lived token exchange failed",
        )
        body = self._parse_response(
            response,
            error_message="Instagram long-lived token exchange failed",
        )

        access_token = body.get("access_token")
        if not access_token:
            raise InstagramApiError("Instagram long-lived token response is incomplete")

        return InstagramTokenResult(
            access_token=str(access_token),
            instagram_user_id=instagram_user_id,
            expires_at=self._expires_at(body.get("expires_in")),
        )

    def refresh_long_lived_token(
        self,
        *,
        access_token: str,
        instagram_user_id: str,
    ) -> InstagramTokenResult:
        response = self._get_response(
            settings.instagram_refresh_token_url,
            params={
                "grant_type": "ig_refresh_token",
                "access_token": access_token,
            },
            error_message="Instagram token refresh failed",
        )
        body = self._parse_response(
            response,
            error_message="Instagram token refresh failed",
        )

        refreshed_token = body.get("access_token")
        if not refreshed_token:
            raise InstagramApiError("Instagram token refresh response is incomplete")

        return InstagramTokenResult(
            access_token=str(refreshed_token),
            instagram_user_id=instagram_user_id,
            expires_at=self._expires_at(body.get("expires_in")),
        )

    def get_profile(self, access_token: str, instagram_user_id: str) -> InstagramProfile:
        response = self._get_response(
            f"{settings.instagram_graph_url}/{instagram_user_id}",
            params={
                "fields": "id,username",
                "access_token": access_token,
            },
            error_message="Instagram profile request failed",
        )
        body = self._parse_response(
            response,
            error_message="Instagram profile request failed",
        )

        return InstagramProfile(
            instagram_user_id=str(body.get("id", instagram_user_id)),
            username=body.get("username"),
        )

    def list_media(
        self,
        *,
        access_token: str,
        instagram_user_id: str,
    ) -> list[InstagramMediaItem]:
        url = f"{settings.instagram_graph_url}/{instagram_user_id}/media"
        params: dict[str, str] | None = {
            "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp",
            "access_token": access_token,
        }
        items: list[InstagramMediaItem] = []

        while url:
            body = self._get_json(
                url,
                params=params,
                error_message="Instagram media request failed",
            )
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
            body = self._get_json(
                url,
                params=params,
                error_message="Instagram comments request failed",
            )
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
        response = self._get_response(
            url,
            params=params,
            error_message=error_message,
        )
        return self._parse_response(response, error_message=error_message)

    def _get_response(
        self,
        url: str,
        *,
        params: dict[str, str] | None,
        error_message: str,
    ) -> httpx.Response:
        try:
            return self.http.get(url, params=params)
        except httpx.HTTPError as exc:
            raise InstagramApiError(error_message) from exc

    def _post_response(
        self,
        url: str,
        *,
        data: dict[str, str],
        error_message: str,
    ) -> httpx.Response:
        try:
            return self.http.post(url, data=data)
        except httpx.HTTPError as exc:
            raise InstagramApiError(error_message) from exc

    @staticmethod
    def _parse_response(response: httpx.Response, *, error_message: str) -> dict:
        try:
            body = response.json()
        except ValueError as exc:
            raise InstagramApiError(
                error_message,
                status_code=response.status_code,
            ) from exc

        if response.is_error:
            raw_error = body.get("error", {}) if isinstance(body, dict) else {}
            message = raw_error.get("message") or error_message
            code = raw_error.get("code")
            subcode = raw_error.get("error_subcode")
            trace_id = raw_error.get("fbtrace_id")
            raise InstagramApiError(
                str(message),
                status_code=response.status_code,
                code=str(code) if code is not None else None,
                subcode=str(subcode) if subcode is not None else None,
                trace_id=str(trace_id) if trace_id is not None else None,
            )

        if not isinstance(body, dict):
            raise InstagramApiError(
                error_message,
                status_code=response.status_code,
            )
        return body

    @staticmethod
    def _expires_at(expires_in) -> datetime | None:
        if expires_in is None:
            return None
        try:
            seconds = int(expires_in)
        except (TypeError, ValueError):
            return None
        return datetime.now(timezone.utc) + timedelta(seconds=seconds)

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
