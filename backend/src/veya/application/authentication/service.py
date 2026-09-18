from dataclasses import dataclass

from sqlalchemy.orm import Session

from veya.application.authentication.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from veya.domain.users.models import User
from veya.infrastructure.security.passwords import hash_password, verify_password
from veya.infrastructure.security.tokens import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from veya.repositories.refresh_tokens import RefreshTokenRepository
from veya.repositories.users import UserRepository


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthenticationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def signup(self, *, email: str, password: str) -> tuple[User, TokenPair]:
        if self.users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError("Email is already registered")

        user = self.users.create(
            email=email,
            password_hash=hash_password(password),
        )
        tokens = self._issue_token_pair(user)
        self.db.commit()
        self.db.refresh(user)
        return user, tokens

    def login(self, *, email: str, password: str) -> tuple[User, TokenPair]:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        if not user.is_active:
            raise InactiveUserError("User account is inactive")

        tokens = self._issue_token_pair(user)
        self.db.commit()
        return user, tokens

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except InvalidTokenError as exc:
            raise InvalidRefreshTokenError(str(exc)) from exc

        stored = self.refresh_tokens.get_by_jti(payload.jti)
        if stored is None or stored.is_revoked:
            raise InvalidRefreshTokenError("Refresh token is revoked or unknown")

        user = self.users.get_by_uuid(payload.subject)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError("Refresh token user is unavailable")

        self.refresh_tokens.revoke(stored)
        tokens = self._issue_token_pair(user)
        self.db.commit()
        return tokens

    def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except InvalidTokenError:
            return

        stored = self.refresh_tokens.get_by_jti(payload.jti)
        if stored is None or stored.is_revoked:
            return

        self.refresh_tokens.revoke(stored)
        self.db.commit()

    def get_user_from_access_token(self, token: str) -> User:
        try:
            payload = decode_token(token, expected_type="access")
        except InvalidTokenError as exc:
            raise InvalidCredentialsError(str(exc)) from exc

        user = self.users.get_by_uuid(payload.subject)
        if user is None or not user.is_active:
            raise InvalidCredentialsError("User is unavailable")
        return user

    def _issue_token_pair(self, user: User) -> TokenPair:
        access_token, _ = create_access_token(user.uuid)
        refresh_token, refresh_payload = create_refresh_token(user.uuid)
        self.refresh_tokens.create(
            user_id=user.id,
            jti=refresh_payload.jti,
            expires_at=refresh_payload.expires_at,
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)
