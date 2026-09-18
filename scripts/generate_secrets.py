#!/usr/bin/env python3
import base64
import secrets


def token(bytes_count: int = 32) -> str:
    return secrets.token_urlsafe(bytes_count)


def fernet_key() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()


def main() -> None:
    print("# Generated locally. Store these in your secret manager; do not commit them.")
    print(f"POSTGRES_PASSWORD={token(24)}")
    print(f"REDIS_PASSWORD={token(24)}")
    print(f"JWT_SECRET_KEY={token(48)}")
    print(f"INSTAGRAM_TOKEN_ENCRYPTION_KEY={fernet_key()}")


if __name__ == "__main__":
    main()
