from dataclasses import dataclass

from sqlalchemy.orm import Session

from veya.application.instagram.connection_health import (
    InstagramConnectionHealthError,
    InstagramConnectionHealthService,
)
from veya.domain.instagram.models import InstagramAccount, InstagramMedia
from veya.domain.users.models import User
from veya.infrastructure.instagram.client import InstagramApiError, InstagramClient
from veya.repositories.instagram_accounts import InstagramAccountRepository
from veya.repositories.instagram_comments import InstagramCommentRepository
from veya.repositories.instagram_media import InstagramMediaRepository


class InstagramSyncError(RuntimeError):
    pass


@dataclass(frozen=True)
class InstagramSyncResult:
    media_count: int
    comment_count: int


class InstagramSyncService:
    def __init__(self, db: Session, client: InstagramClient | None = None) -> None:
        self.db = db
        self.client = client or InstagramClient()
        self.accounts = InstagramAccountRepository(db)
        self.media = InstagramMediaRepository(db)
        self.comments = InstagramCommentRepository(db)
        self.health = InstagramConnectionHealthService(
            db,
            client=self.client,
        )

    def sync_account(self, *, user: User, account_id: int) -> InstagramSyncResult:
        account = self._get_owned_account(user=user, account_id=account_id)

        try:
            access_token = self.health.access_token_for_sync(
                user=user,
                account_id=account.id,
            )
        except InstagramConnectionHealthError as exc:
            raise InstagramSyncError(str(exc)) from exc

        try:
            remote_media = self.client.list_media(
                access_token=access_token,
                instagram_user_id=account.instagram_user_id,
            )
        except InstagramApiError as exc:
            self.health.record_api_error(
                user=user,
                account_id=account.id,
                error=exc,
            )
            raise InstagramSyncError(str(exc)) from exc

        media_count = 0
        comment_count = 0

        for remote in remote_media:
            media = self.media.upsert(
                instagram_account_id=account.id,
                instagram_media_id=remote.media_id,
                media_type=remote.media_type,
                caption=remote.caption,
                media_url=remote.media_url,
                thumbnail_url=remote.thumbnail_url,
                permalink=remote.permalink,
                posted_at=remote.timestamp,
            )
            media_count += 1

            try:
                remote_comments = self.client.list_comments(
                    access_token=access_token,
                    instagram_media_id=remote.media_id,
                )
            except InstagramApiError as exc:
                self.health.record_api_error(
                    user=user,
                    account_id=account.id,
                    error=exc,
                )
                raise InstagramSyncError(str(exc)) from exc

            for remote_comment in remote_comments:
                self.comments.upsert(
                    instagram_media_id=media.id,
                    instagram_comment_id=remote_comment.comment_id,
                    text=remote_comment.text,
                    username=remote_comment.username,
                    commented_at=remote_comment.timestamp,
                )
                comment_count += 1

        self.health.record_success(user=user, account_id=account.id)
        self.db.commit()
        return InstagramSyncResult(media_count=media_count, comment_count=comment_count)

    def list_media(self, *, user: User, account_id: int) -> list[InstagramMedia]:
        account = self._get_owned_account(user=user, account_id=account_id)
        return self.media.get_by_account_id(account.id)

    def list_comments(
        self,
        *,
        user: User,
        account_id: int,
        media_id: int,
    ):
        account = self._get_owned_account(user=user, account_id=account_id)
        media = next(
            (
                item
                for item in self.media.get_by_account_id(account.id)
                if item.id == media_id
            ),
            None,
        )
        if media is None:
            raise InstagramSyncError("Instagram media not found")
        return self.comments.get_by_media_id(media.id)

    def _get_owned_account(self, *, user: User, account_id: int) -> InstagramAccount:
        account = self.accounts.get_by_id(account_id)
        if account is None or account.user_id != user.id:
            raise InstagramSyncError("Instagram account not found")
        return account
