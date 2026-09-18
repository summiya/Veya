from dataclasses import dataclass

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
        return self.client.build_authorization_url(state=state)

    def connect_from_callback(self, *, code: str, state: str) -> InstagramConnectionResult:
        try:
            user_uuid = decode_instagram_oauth_state(state)
        except InvalidOAuthStateError as exc:
            raise InstagramConnectionError(str(exc)) from exc

        user = self.users.get_by_uuid(user_uuid)
        if user is None or not user.is_active:
            raise InstagramConnectionError("Veya user is unavailable")

        try:
            token = self.client.exchange_code(code)
            profile = self.client.get_profile(
                token.access_token,
                token.instagram_user_id,
            )
        except InstagramApiError as exc:
            raise InstagramConnectionError(str(exc)) from exc

        account = self.accounts.upsert(
            user_id=user.id,
            instagram_user_id=profile.instagram_user_id,
            username=profile.username,
            access_token_encrypted=encrypt_instagram_token(token.access_token),
            token_expires_at=token.expires_at,
        )
        self.db.commit()
        self.db.refresh(account)
        return InstagramConnectionResult(account=account)

    def list_accounts(self, user: User) -> list[InstagramAccount]:
        return self.accounts.get_by_user_id(user.id)
