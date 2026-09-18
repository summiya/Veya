from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from veya.domain.instagram.models import InstagramAccount


class InstagramAccountRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, account_id: int) -> InstagramAccount | None:
        return self.db.get(InstagramAccount, account_id)

    def get_by_user_id(self, user_id: int) -> list[InstagramAccount]:
        return list(
            self.db.scalars(
                select(InstagramAccount)
                .where(InstagramAccount.user_id == user_id)
                .order_by(InstagramAccount.id.asc())
            )
        )

    def list_due_for_sync(self, now: datetime) -> list[InstagramAccount]:
        return list(
            self.db.scalars(
                select(InstagramAccount)
                .where(
                    InstagramAccount.connection_status == "connected",
                    InstagramAccount.sync_status != "running",
                    or_(
                        InstagramAccount.next_sync_at.is_(None),
                        InstagramAccount.next_sync_at <= now,
                    ),
                )
                .order_by(InstagramAccount.id.asc())
            )
        )

    def get_by_user_and_instagram_id(
        self,
        *,
        user_id: int,
        instagram_user_id: str,
    ) -> InstagramAccount | None:
        return self.db.scalar(
            select(InstagramAccount).where(
                InstagramAccount.user_id == user_id,
                InstagramAccount.instagram_user_id == instagram_user_id,
            )
        )

    def upsert(
        self,
        *,
        user_id: int,
        instagram_user_id: str,
        username: str | None,
        access_token_encrypted: str,
        token_expires_at,
    ) -> InstagramAccount:
        account = self.get_by_user_and_instagram_id(
            user_id=user_id,
            instagram_user_id=instagram_user_id,
        )

        if account is None:
            account = InstagramAccount(
                user_id=user_id,
                instagram_user_id=instagram_user_id,
                username=username,
                access_token_encrypted=access_token_encrypted,
                token_expires_at=token_expires_at,
            )
            self.db.add(account)
        else:
            account.username = username
            account.access_token_encrypted = access_token_encrypted
            account.token_expires_at = token_expires_at

        account.connection_status = "connected"
        account.last_api_error_code = None
        account.last_api_error_message = None
        self.db.flush()
        return account

    def delete(self, account: InstagramAccount) -> None:
        self.db.delete(account)
        self.db.flush()
