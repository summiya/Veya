from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from veya.domain.authentication.models import PasswordResetToken


class PasswordResetTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(token)
        self.db.flush()
        return token

    def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        return self.db.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash
            )
        )

    def invalidate_active_for_user(self, user_id: int) -> None:
        now = datetime.now(timezone.utc)
        self.db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=now)
        )
        self.db.flush()

    def mark_used(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        self.db.flush()
