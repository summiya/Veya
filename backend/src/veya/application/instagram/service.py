from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from veya.domain.instagram.models import InstagramAccount
from veya.domain.users.models import User
from veya.infrastructure.instagram.client import InstagramApiError, InstagramClient
from veya.infrastructure.instagram.oauth_state import (
    InvalidOAuthStateError,
    create_instagram_oauth_state,
    decode_instagram_oauth_state,
)
from veya.infrastructure.instagram.token_cipher import encrypt_instagram_token
from veya.repositories.instagram_accounts import InstagramAccountRepository
from veya.repositories.users import UserRepository


class InstagramConnectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class InstagramConnectionResult:
    account: InstagramAccount


@dataclass(frozen=True)
class InstagramReadiness:
    configured: bool
    missing_settings: list[str]
    redirect_uri: str
    scopes: list[str]


class InstagramConnectionService:
    def __init__(
        self,
        db: Session,
        client: InstagramClient | None = None,
    ) -> None:
        self.db = db
        self.client = client or InstagramClient()
        self.accounts = InstagramAccountRepository(db)
        self.users = UserRepository(db)

    def authorization_url(self, user: User) -> str:
        state = create_instagram_oauth_state(user.uuid)
        try:
            return self.client.build_authorization_url(state=state)
        except InstagramApiError as exc:
            raise InstagramConnectionError(str(exc)) from exc

    def connect_from_callback(self, *, code: str, state: str) -> InstagramConnectionResult:
        try:
            user_uuid = decode_instagram_oauth_state(state)
        except InvalidOAuthStateError as exc:
            raise InstagramConnectionError(str(exc)) from exc

        user = self.users.get_by_uuid(user_uuid)
        if user is None or not user.is_active:
            raise InstagramConnectionError("Veya user is unavailable")

        try:
            short_lived = self.client.exchange_code(code)
            token = self.client.exchange_long_lived_token(
                short_lived_token=short_lived.access_token,
                instagram_user_id=short_lived.instagram_user_id,
            )
            profile = self.client.get_profile(
                token.access_token,
                token.instagram_user_id,
            )
        except InstagramApiError as exc:
            raise InstagramConnectionError(str(exc)) from exc

        now = datetime.now(timezone.utc)
        account = self.accounts.upsert(
            user_id=user.id,
            instagram_user_id=profile.instagram_user_id,
            username=profile.username,
            access_token_encrypted=encrypt_instagram_token(token.access_token),
            token_expires_at=token.expires_at,
        )
        account.connection_status = "connected"
        account.last_connection_check_at = now
        account.last_token_refreshed_at = now
        account.last_api_error_code = None
        account.last_api_error_message = None
        self.db.commit()
        self.db.refresh(account)
        return InstagramConnectionResult(account=account)

    def list_accounts(self, user: User) -> list[InstagramAccount]:
        return self.accounts.get_by_user_id(user.id)

    def disconnect(self, *, user: User, account_id: int) -> None:
        account = self.accounts.get_by_id(account_id)
        if account is None or account.user_id != user.id:
            raise InstagramConnectionError("Instagram account not found")

        self.accounts.delete(account)
        self.db.commit()

    @staticmethod
    def readiness() -> InstagramReadiness:
        from veya.core.config import settings

        required = {
            "INSTAGRAM_CLIENT_ID": settings.instagram_client_id,
            "INSTAGRAM_CLIENT_SECRET": settings.instagram_client_secret,
            "INSTAGRAM_REDIRECT_URI": settings.instagram_redirect_uri,
            "INSTAGRAM_TOKEN_ENCRYPTION_KEY": settings.instagram_token_encryption_key,
        }
        missing = [name for name, value in required.items() if not value]

        if (
            settings.environment.lower() == "production"
            and not settings.instagram_redirect_uri.startswith("https://")
        ):
            missing.append("INSTAGRAM_REDIRECT_URI_HTTPS")

        return InstagramReadiness(
            configured=not missing,
            missing_settings=missing,
            redirect_uri=settings.instagram_redirect_uri,
            scopes=[
                scope.strip()
                for scope in settings.instagram_scopes.split(",")
                if scope.strip()
            ],
        )
