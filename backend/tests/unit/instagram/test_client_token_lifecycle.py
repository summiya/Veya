from datetime import datetime, timezone
from urllib.parse import parse_qs

import httpx
import pytest

from veya.core.config import settings
from veya.infrastructure.instagram.client import InstagramApiError, InstagramClient


def test_exchanges_short_lived_token_for_long_lived_token() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(
            200,
            json={
                "access_token": "long-lived-token",
                "token_type": "bearer",
                "expires_in": 5184000,
            },
        )

    client = InstagramClient(
        http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    result = client.exchange_long_lived_token(
        short_lived_token="short-lived-token",
        instagram_user_id="ig-123",
    )

    query = parse_qs(httpx.URL(captured["url"]).query.decode())
    assert query["grant_type"] == ["ig_exchange_token"]
    assert query["client_secret"] == [settings.instagram_client_secret]
    assert query["access_token"] == ["short-lived-token"]
    assert result.access_token == "long-lived-token"
    assert result.instagram_user_id == "ig-123"
    assert result.expires_at is not None
    assert result.expires_at > datetime.now(timezone.utc)


def test_refreshes_long_lived_token() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(
            200,
            json={
                "access_token": "refreshed-token",
                "token_type": "bearer",
                "expires_in": 5184000,
            },
        )

    client = InstagramClient(
        http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    result = client.refresh_long_lived_token(
        access_token="existing-token",
        instagram_user_id="ig-123",
    )

    query = parse_qs(httpx.URL(captured["url"]).query.decode())
    assert query["grant_type"] == ["ig_refresh_token"]
    assert query["access_token"] == ["existing-token"]
    assert result.access_token == "refreshed-token"
    assert result.expires_at is not None


def test_meta_oauth_error_exposes_reconnect_signal() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "message": "Invalid OAuth access token.",
                    "type": "OAuthException",
                    "code": 190,
                    "error_subcode": 463,
                    "fbtrace_id": "trace-123",
                }
            },
        )

    client = InstagramClient(
        http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    with pytest.raises(InstagramApiError) as caught:
        client.get_profile("bad-token", "ig-123")

    assert caught.value.code == "190"
    assert caught.value.subcode == "463"
    assert caught.value.trace_id == "trace-123"
    assert caught.value.requires_reconnect is True


def test_rate_limit_error_is_retryable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={"error": {"message": "Too many calls", "code": 4}},
        )

    client = InstagramClient(
        http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    with pytest.raises(InstagramApiError) as caught:
        client.get_profile("token", "ig-123")

    assert caught.value.retryable is True
    assert caught.value.requires_reconnect is False
