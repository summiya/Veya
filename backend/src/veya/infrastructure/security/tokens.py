from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from veya.core.config import settings


class InvalidTokenError(ValueError):
    pass


@dataclass(frozen=True)
class TokenPayload:
    subject: str
    token_type: str
    jti: str
    expires_at: datetime


def _create_token(*, subject: str, token_type: str, expires_delta: timedelta) -> tuple[str, TokenPayload]:
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    jti = str(uuid4())
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }
    encoded = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded, TokenPayload(subject, token_type, jti, expires_at)


def create_access_token(subject: str) -> tuple[str, TokenPayload]:
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str) -> tuple[str, TokenPayload]:
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid or expired token") from exc

    subject = payload.get("sub")
    token_type = payload.get("type")
    jti = payload.get("jti")
    exp = payload.get("exp")

    if not subject or token_type != expected_type or not jti or not exp:
        raise InvalidTokenError("Invalid token payload")

    return TokenPayload(
        subject=str(subject),
        token_type=str(token_type),
        jti=str(jti),
        expires_at=datetime.fromtimestamp(int(exp), tz=timezone.utc),
    )
