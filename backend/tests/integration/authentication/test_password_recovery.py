import hashlib
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from sqlalchemy import select

from veya.application.authentication.password_recovery import PasswordRecoveryService
from veya.domain.authentication.models import PasswordResetToken
from veya.infrastructure.mailer.provider import MailMessage


EMAIL = "creator@example.com"
PASSWORD = "strong-password-123"
NEW_PASSWORD = "new-strong-password-456"


class FakeMailer:
    def __init__(self) -> None:
        self.messages: list[MailMessage] = []

    def send(self, message: MailMessage) -> None:
        self.messages.append(message)


def signup(client) -> dict:
    response = client.post(
        "/api/auth/signup",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()


def extract_reset_token(message: MailMessage) -> str:
    marker = "/reset-password?token="
    start = message.html.index(marker) + len(marker)
    end = message.html.index('"', start)
    return message.html[start:end]


def test_recovery_stores_only_token_hash_and_resets_password(client, db) -> None:
    auth = signup(client)
    mailer = FakeMailer()

    PasswordRecoveryService(db, mailer=mailer).request_reset(email=EMAIL)

    assert len(mailer.messages) == 1
    raw_token = extract_reset_token(mailer.messages[0])

    stored = db.scalar(select(PasswordResetToken))
    assert stored is not None
    assert stored.token_hash == hashlib.sha256(raw_token.encode()).hexdigest()
    assert raw_token not in stored.token_hash

    reset = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "password": NEW_PASSWORD},
    )
    assert reset.status_code == 200

    old_login = client.post(
        "/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={"email": EMAIL, "password": NEW_PASSWORD},
    )
    assert new_login.status_code == 200

    reused = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "password": "another-password-789"},
    )
    assert reused.status_code == 400

    old_refresh = client.post(
        "/api/auth/refresh",
        json={"refresh_token": auth["refresh_token"]},
    )
    assert old_refresh.status_code == 401


def test_new_reset_request_invalidates_previous_link(client, db) -> None:
    signup(client)
    first_mailer = FakeMailer()
    second_mailer = FakeMailer()

    PasswordRecoveryService(db, mailer=first_mailer).request_reset(email=EMAIL)
    first_token = extract_reset_token(first_mailer.messages[0])

    PasswordRecoveryService(db, mailer=second_mailer).request_reset(email=EMAIL)
    second_token = extract_reset_token(second_mailer.messages[0])

    first = client.post(
        "/api/auth/reset-password",
        json={"token": first_token, "password": NEW_PASSWORD},
    )
    second = client.post(
        "/api/auth/reset-password",
        json={"token": second_token, "password": NEW_PASSWORD},
    )

    assert first.status_code == 400
    assert second.status_code == 200


def test_expired_reset_token_is_rejected(client, db) -> None:
    signup(client)
    mailer = FakeMailer()

    PasswordRecoveryService(db, mailer=mailer).request_reset(email=EMAIL)
    raw_token = extract_reset_token(mailer.messages[0])

    stored = db.scalar(select(PasswordResetToken))
    assert stored is not None
    stored.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()

    response = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "password": NEW_PASSWORD},
    )

    assert response.status_code == 400


def test_forgot_password_does_not_reveal_account_existence(client) -> None:
    known = client.post(
        "/api/auth/forgot-password",
        json={"email": "missing@example.com"},
    )

    assert known.status_code == 200
    assert known.json() == {
        "message": (
            "If an active Veya account exists for that email, "
            "a password reset link has been sent."
        )
    }
