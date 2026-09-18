from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from veya.core.config import settings


class InvalidOAuthStateError(ValueError):
    pass


def create_instagram_oauth_state(user_uuid: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_uuid,
        "type": "instagram_oauth_state",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_instagram_oauth_state(state: str) -> str:
    try:
        payload = jwt.decode(
            state,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise InvalidOAuthStateError("Invalid or expired Instagram OAuth state") from exc

    if payload.get("type") != "instagram_oauth_state" or not payload.get("sub"):
        raise InvalidOAuthStateError("Invalid Instagram OAuth state")

    return str(payload["sub"])
