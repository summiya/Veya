from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from veya.core.config import settings
from veya.domain.instagram.models import InstagramAccount
from veya.domain.users.models import User
from veya.infrastructure.instagram.client import InstagramApiError, InstagramClient
from veya.infrastructure.instagram.token_cipher import (
    decrypt_instagram_token,
    encrypt_instagram_token,
)
from veya.repositories.instagram_accounts import InstagramAccountRepository


class InstagramConnectionHealthError(RuntimeError):
    def __init__(self, message: str, *, reconnect_required: bool = False) -> None:
        super().__init__(message)
        self.reconnect_required = reconnect_required


@dataclass(frozen=True)
class InstagramConnectionCheck:
    account: InstagramAccount
    token_refreshed: bool


class InstagramConnectionHealthService:
    def __init__(
        self,
        db: Session,
        client: InstagramClient | None = None,
    ) -> None:
        self.db = db
        self.client = client or InstagramClient()
        self.accounts = InstagramAccountRepository(db)

    def access_token_for_sync(
        self,
        *,
        user: User,
        account_id: int,
    ) -> str:
        account = self._get_owned_account(user=user, account_id=account_id)
        return self._ensure_current_token(account=account, force=False)[0]

    def check_connection(
        self,
        *,
        user: User,
        account_id: int,
    ) -> InstagramConnectionCheck:
        account = self._get_owned_account(user=user, account_id=account_id)
        access_token, refreshed = self._ensure_current_token(
            account=account,
            force=False,
        )

        try:
            profile = self.client.get_profile(
                access_token,
                account.instagram_user_id,
            )
        except InstagramApiError as exc:
            self._record_error(account=account, error=exc, checked=True)
            raise InstagramConnectionHealthError(
                str(exc),
                reconnect_required=exc.requires_reconnect,
            ) from exc

        account.username = profile.username
        account.connection_status = "connected"
        account.last_connection_check_at = datetime.now(timezone.utc)
        account.last_api_error_code = None
        account.last_api_error_message = None
        self.db.commit()
        self.db.refresh(account)
        return InstagramConnectionCheck(account=account, token_refreshed=refreshed)

    def record_api_error(
        self,
        *,
        user: User,
        account_id: int,
        error: InstagramApiError,
    ) -> None:
        account = self._get_owned_account(user=user, account_id=account_id)
        self._record_error(account=account, error=error, checked=False)

    def record_success(
        self,
        *,
        user: User,
        account_id: int,
    ) -> None:
        account = self._get_owned_account(user=user, account_id=account_id)
        account.connection_status = "connected"
        account.last_api_error_code = None
        account.last_api_error_message = None
        self.db.commit()

    def refresh_token(
        self,
        *,
        user: User,
        account_id: int,
    ) -> InstagramConnectionCheck:
        account = self._get_owned_account(user=user, account_id=account_id)
        now = datetime.now(timezone.utc)
        last_refresh = self._aware(account.last_token_refreshed_at)

        if last_refresh is not None and last_refresh > now - timedelta(hours=24):
            return InstagramConnectionCheck(
                account=account,
                token_refreshed=False,
            )

        _, refreshed = self._ensure_current_token(account=account, force=True)
        self.db.refresh(account)
        return InstagramConnectionCheck(
            account=account,
            token_refreshed=refreshed,
        )

    def _ensure_current_token(
        self,
        *,
        account: InstagramAccount,
        force: bool,
    ) -> tuple[str, bool]:
        now = datetime.now(timezone.utc)
        expires_at = self._aware(account.token_expires_at)

        if expires_at is not None and expires_at <= now:
            account.connection_status = "reconnect_required"
            account.sync_status = "failed"
            account.next_sync_at = None
            account.last_api_error_code = "token_expired"
            account.last_api_error_message = "Instagram access token has expired"
            self.db.commit()
            raise InstagramConnectionHealthError(
                "Instagram access token has expired; reconnect the account",
                reconnect_required=True,
            )

        refresh_before = now + timedelta(
            days=settings.instagram_token_refresh_before_days
        )
        should_refresh = force or (
            expires_at is not None and expires_at <= refresh_before
        )

        access_token = decrypt_instagram_token(account.access_token_encrypted)
        if not should_refresh:
            return access_token, False

        try:
            refreshed = self.client.refresh_long_lived_token(
                access_token=access_token,
                instagram_user_id=account.instagram_user_id,
            )
        except InstagramApiError as exc:
            self._record_error(account=account, error=exc, checked=False)
            raise InstagramConnectionHealthError(
                str(exc),
                reconnect_required=exc.requires_reconnect,
            ) from exc

        account.access_token_encrypted = encrypt_instagram_token(
            refreshed.access_token
        )
        account.token_expires_at = refreshed.expires_at
        account.last_token_refreshed_at = now
        account.connection_status = "connected"
        account.last_api_error_code = None
        account.last_api_error_message = None
        self.db.commit()
        return refreshed.access_token, True

    def _record_error(
        self,
        *,
        account: InstagramAccount,
        error: InstagramApiError,
        checked: bool,
    ) -> None:
        account.connection_status = (
            "reconnect_required" if error.requires_reconnect else "degraded"
        )
        if error.requires_reconnect:
            account.sync_status = "failed"
            account.next_sync_at = None
        if checked:
            account.last_connection_check_at = datetime.now(timezone.utc)
        account.last_api_error_code = (
            error.code
            or (f"http_{error.status_code}" if error.status_code else "instagram_error")
        )
        account.last_api_error_message = str(error)[:4000]
        self.db.commit()

    def _get_owned_account(
        self,
        *,
        user: User,
        account_id: int,
    ) -> InstagramAccount:
        account = self.accounts.get_by_id(account_id)
        if account is None or account.user_id != user.id:
            raise InstagramConnectionHealthError("Instagram account not found")
        return account

    @staticmethod
    def _aware(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
