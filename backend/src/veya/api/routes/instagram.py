from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from veya.api.dependencies.authentication import get_current_user
from veya.api.schemas.instagram import (
    InstagramAccountResponse,
    InstagramCallbackResponse,
    InstagramConnectResponse,
)
from veya.api.schemas.instagram_sync import (
    InstagramCommentResponse,
    InstagramMediaResponse,
    InstagramSyncResponse,
)
from veya.application.instagram.service import (
    InstagramConnectionError,
    InstagramConnectionService,
)
from veya.application.instagram.sync_service import InstagramSyncError, InstagramSyncService
from veya.domain.users.models import User
from veya.core.config import settings
from veya.infrastructure.database.dependencies import get_db


router = APIRouter(prefix="/api/integrations/instagram", tags=["instagram"])


@router.get("/connect", response_model=InstagramConnectResponse)
def connect_instagram(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InstagramConnectResponse:
    authorization_url = InstagramConnectionService(db).authorization_url(current_user)
    return InstagramConnectResponse(authorization_url=authorization_url)


@router.get("/callback")
def instagram_callback(
    code: Annotated[str, Query(min_length=1)],
    state: Annotated[str, Query(min_length=1)],
    db: Annotated[Session, Depends(get_db)],
) -> RedirectResponse:
    try:
        result = InstagramConnectionService(db).connect_from_callback(
            code=code,
            state=state,
        )
    except InstagramConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    redirect_url = (
        f"{settings.frontend_app_url.rstrip('/')}/dashboard"
        f"?instagram=connected&account_id={result.account.id}"
    )
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.get("/accounts", response_model=list[InstagramAccountResponse])
def list_instagram_accounts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[InstagramAccountResponse]:
    accounts = InstagramConnectionService(db).list_accounts(current_user)
    return [InstagramAccountResponse.model_validate(account) for account in accounts]


@router.post("/accounts/{account_id}/sync", response_model=InstagramSyncResponse)
def sync_instagram_account(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InstagramSyncResponse:
    try:
        result = InstagramSyncService(db).sync_account(
            user=current_user,
            account_id=account_id,
        )
    except InstagramSyncError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return InstagramSyncResponse(
        media_count=result.media_count,
        comment_count=result.comment_count,
    )


@router.get(
    "/accounts/{account_id}/media",
    response_model=list[InstagramMediaResponse],
)
def list_instagram_media(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[InstagramMediaResponse]:
    try:
        media = InstagramSyncService(db).list_media(
            user=current_user,
            account_id=account_id,
        )
    except InstagramSyncError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [InstagramMediaResponse.model_validate(item) for item in media]


@router.get(
    "/accounts/{account_id}/media/{media_id}/comments",
    response_model=list[InstagramCommentResponse],
)
def list_instagram_comments(
    account_id: int,
    media_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[InstagramCommentResponse]:
    try:
        comments = InstagramSyncService(db).list_comments(
            user=current_user,
            account_id=account_id,
            media_id=media_id,
        )
    except InstagramSyncError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [InstagramCommentResponse.model_validate(item) for item in comments]
