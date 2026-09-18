from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from veya.api.dependencies.authentication import get_current_user
from veya.api.schemas.background_sync import InstagramSyncJobResponse
from veya.application.background_sync.service import BackgroundSyncError, BackgroundSyncService
from veya.domain.users.models import User
from veya.infrastructure.database.dependencies import get_db


router = APIRouter(prefix="/api/background-sync", tags=["background-sync"])


@router.get(
    "/instagram/accounts/{account_id}/jobs",
    response_model=list[InstagramSyncJobResponse],
)
def list_background_sync_jobs(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[InstagramSyncJobResponse]:
    try:
        jobs = BackgroundSyncService(db).list_jobs(
            user=current_user,
            account_id=account_id,
            limit=limit,
        )
    except BackgroundSyncError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return [InstagramSyncJobResponse.model_validate(job) for job in jobs]
