import hashlib
import html
import logging
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from sqlalchemy.orm import Session

from veya.core.config import settings
from veya.infrastructure.mailer.factory import create_mailer
from veya.infrastructure.mailer.provider import MailMessage, Mailer
from veya.infrastructure.security.passwords import hash_password
from veya.repositories.password_reset_tokens import PasswordResetTokenRepository
from veya.repositories.refresh_tokens import RefreshTokenRepository
from veya.repositories.users import UserRepository


logger = logging.getLogger(__name__)


class InvalidPasswordResetTokenError(ValueError):
    pass


class PasswordRecoveryService:
    def __init__(self, db: Session, mailer: Mailer | None = None) -> None:
        self.db = db
        self.mailer = mailer or create_mailer()
        self.users = UserRepository(db)
        self.reset_tokens = PasswordResetTokenRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def request_reset(self, *, email: str) -> None:
        user = self.users.get_by_email(email)

        # Always return the same API response for unknown/inactive accounts.
        if user is None or not user.is_active:
            return

        self.reset_tokens.invalidate_active_for_user(user.id)

        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.password_reset_expire_minutes
        )
        stored_token = self.reset_tokens.create(
            user_id=user.id,
            token_hash=self._hash_token(raw_token),
            expires_at=expires_at,
        )
        self.db.commit()

        reset_url = (
            f"{settings.frontend_app_url.rstrip('/')}/reset-password"
            f"?token={quote(raw_token)}"
        )
        safe_url = html.escape(reset_url, quote=True)

        try:
            self.mailer.send(
                MailMessage(
                    to=user.email,
                    subject="Reset your Veya password",
                    html=(
                        "<p>We received a request to reset your Veya password.</p>"
                        f'<p><a href="{safe_url}">Reset your password</a></p>'
                        f"<p>This link expires in "
                        f"{settings.password_reset_expire_minutes} minutes.</p>"
                        "<p>If you did not request this, you can ignore this email.</p>"
                    ),
                )
            )
        except Exception:
            self.reset_tokens.mark_used(stored_token)
            self.db.commit()
            logger.exception("Password-reset email delivery failed for user_id=%s", user.id)

    def reset_password(self, *, raw_token: str, new_password: str) -> None:
        token = self.reset_tokens.get_by_hash(self._hash_token(raw_token))
        now = datetime.now(timezone.utc)

        if token is None or token.is_used:
            raise InvalidPasswordResetTokenError(
                "Password reset link is invalid or has expired"
            )

        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now:
            raise InvalidPasswordResetTokenError(
                "Password reset link is invalid or has expired"
            )

        user = token.user
        if user is None or not user.is_active:
            raise InvalidPasswordResetTokenError(
                "Password reset link is invalid or has expired"
            )

        user.password_hash = hash_password(new_password)
        self.reset_tokens.invalidate_active_for_user(user.id)
        self.refresh_tokens.revoke_all_for_user(user.id)
        self.db.commit()

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()
