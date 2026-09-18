from fastapi.testclient import TestClient


EMAIL = "creator@example.com"
PASSWORD = "strong-password-123"


def signup(client: TestClient) -> dict:
    response = client.post(
        "/api/auth/signup",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()


def test_signup_creates_user_and_returns_tokens(client: TestClient) -> None:
    body = signup(client)

    assert body["user"]["email"] == EMAIL
    assert body["user"]["is_active"] is True
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_signup_rejects_duplicate_email(client: TestClient) -> None:
    signup(client)

    response = client.post(
        "/api/auth/signup",
        json={"email": EMAIL.upper(), "password": PASSWORD},
    )

    assert response.status_code == 409


def test_signup_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/signup",
        json={"email": EMAIL, "password": "short"},
    )

    assert response.status_code == 422


def test_login_returns_new_token_pair(client: TestClient) -> None:
    signup(client)

    response = client.post(
        "/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == EMAIL
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_rejects_invalid_password(client: TestClient) -> None:
    signup(client)

    response = client.post(
        "/api/auth/login",
        json={"email": EMAIL, "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_me_returns_authenticated_user(client: TestClient) -> None:
    auth = signup(client)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {auth['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == EMAIL


def test_me_requires_access_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_refresh_rotates_refresh_token(client: TestClient) -> None:
    auth = signup(client)
    original_refresh_token = auth["refresh_token"]

    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )

    assert response.status_code == 200
    rotated = response.json()
    assert rotated["access_token"]
    assert rotated["refresh_token"] != original_refresh_token

    reused = client.post(
        "/api/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert reused.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    auth = signup(client)

    response = client.post(
        "/api/auth/logout",
        json={"refresh_token": auth["refresh_token"]},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}

    refreshed = client.post(
        "/api/auth/refresh",
        json={"refresh_token": auth["refresh_token"]},
    )
    assert refreshed.status_code == 401


def test_logout_is_idempotent(client: TestClient) -> None:
    auth = signup(client)
    payload = {"refresh_token": auth["refresh_token"]}

    first = client.post("/api/auth/logout", json=payload)
    second = client.post("/api/auth/logout", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
