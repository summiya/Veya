from cryptography.fernet import Fernet, InvalidToken

from veya.core.config import settings


class InstagramTokenCipherError(RuntimeError):
    pass


def _fernet() -> Fernet:
    key = settings.instagram_token_encryption_key.encode()
    if not key:
        raise InstagramTokenCipherError(
            "INSTAGRAM_TOKEN_ENCRYPTION_KEY must be configured before storing Instagram tokens"
        )

    try:
        return Fernet(key)
    except (ValueError, TypeError) as exc:
        raise InstagramTokenCipherError(
            "INSTAGRAM_TOKEN_ENCRYPTION_KEY is not a valid Fernet key"
        ) from exc


def encrypt_instagram_token(token: str) -> str:
    return _fernet().encrypt(token.encode()).decode()


def decrypt_instagram_token(encrypted_token: str) -> str:
    try:
        return _fernet().decrypt(encrypted_token.encode()).decode()
    except InvalidToken as exc:
        raise InstagramTokenCipherError("Unable to decrypt Instagram access token") from exc
