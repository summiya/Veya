from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from veya.infrastructure.instagram.client import InstagramProfile, InstagramTokenResult


EMAIL = "creator@example.com"
PASSWORD = "strong-password-123"


def signup(client: TestClient) -> dict:
    response = client.post(
        "/api/auth/signup",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth['access_token']}"}


def test_connect_requires_authenticated_user(client: TestClient) -> None:
    response = client.get("/api/integrations/instagram/connect")

    assert response.status_code == 401


def test_connect_returns_authorization_url(client: TestClient) -> None:
    auth = signup(client)

    response = client.get(
        "/api/integrations/instagram/connect",
        headers=auth_headers(auth),
    )

    assert response.status_code == 200
    authorization_url = response.json()["authorization_url"]
    parsed = urlparse(authorization_url)
    query = parse_qs(parsed.query)

    assert query["response_type"] == ["code"]
    assert query["scope"] == [
        "instagram_business_basic,instagram_business_manage_comments"
    ]
    assert query["state"][0]


def test_callback_persists_connected_account(
    client: TestClient,
    monkeypatch,
) -> None:
    auth = signup(client)

    connect = client.get(
        "/api/integrations/instagram/connect",
        headers=auth_headers(auth),
    )
    state = parse_qs(urlparse(connect.json()["authorization_url"]).query)["state"][0]

    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.exchange_code",
        lambda self, code: InstagramTokenResult(
            access_token="fake-test-access-token",
            instagram_user_id="ig-123",
            expires_at=None,
        ),
    )
    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.get_profile",
        lambda self, access_token, instagram_user_id: InstagramProfile(
            instagram_user_id="ig-123",
            username="veya_creator",
        ),
    )

    callback = client.get(
        "/api/integrations/instagram/callback",
        params={"code": "fake-oauth-code", "state": state},
    )

    assert callback.status_code == 200
    assert callback.json()["account"]["instagram_user_id"] == "ig-123"
    assert callback.json()["account"]["username"] == "veya_creator"

    accounts = client.get(
        "/api/integrations/instagram/accounts",
        headers=auth_headers(auth),
    )

    assert accounts.status_code == 200
    assert accounts.json()[0]["instagram_user_id"] == "ig-123"
    assert "access_token" not in accounts.json()[0]
    assert "access_token_encrypted" not in accounts.json()[0]


def test_callback_rejects_invalid_state(client: TestClient) -> None:
    response = client.get(
        "/api/integrations/instagram/callback",
        params={"code": "fake-oauth-code", "state": "invalid-state"},
    )

    assert response.status_code == 400


def test_accounts_are_scoped_to_authenticated_user(
    client: TestClient,
    monkeypatch,
) -> None:
    first = signup(client)

    connect = client.get(
        "/api/integrations/instagram/connect",
        headers=auth_headers(first),
    )
    state = parse_qs(urlparse(connect.json()["authorization_url"]).query)["state"][0]

    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.exchange_code",
        lambda self, code: InstagramTokenResult(
            access_token="fake-test-access-token",
            instagram_user_id="ig-123",
            expires_at=None,
        ),
    )
    monkeypatch.setattr(
        "veya.infrastructure.instagram.client.InstagramClient.get_profile",
        lambda self, access_token, instagram_user_id: InstagramProfile(
            instagram_user_id="ig-123",
            username="veya_creator",
        ),
    )

    callback = client.get(
        "/api/integrations/instagram/callback",
        params={"code": "fake-oauth-code", "state": state},
    )
    assert callback.status_code == 200

    second_signup = client.post(
        "/api/auth/signup",
        json={"email": "second@example.com", "password": PASSWORD},
    )
    assert second_signup.status_code == 201

    accounts = client.get(
        "/api/integrations/instagram/accounts",
        headers=auth_headers(second_signup.json()),
    )

    assert accounts.status_code == 200
    assert accounts.json() == []
