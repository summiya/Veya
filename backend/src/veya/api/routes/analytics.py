from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from veya.api.dependencies.authentication import get_current_user
from veya.api.schemas.analytics import (
    AudienceHealthSnapshotResponse,
    AudienceTrendResponse,
)
from veya.application.analytics.service import AnalyticsError, AnalyticsService
from veya.domain.users.models import User
from veya.infrastructure.database.dependencies import get_db


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.post(
    "/instagram/accounts/{account_id}/snapshots",
    response_model=AudienceHealthSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
def capture_audience_health_snapshot(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AudienceHealthSnapshotResponse:
    try:
        snapshot = AnalyticsService(db).capture_snapshot(
            user=current_user,
            account_id=account_id,
        )
    except AnalyticsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return AudienceHealthSnapshotResponse.model_validate(snapshot)


@router.get(
    "/instagram/accounts/{account_id}/trends",
    response_model=AudienceTrendResponse,
)
def get_audience_health_trends(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> AudienceTrendResponse:
    try:
        result = AnalyticsService(db).trend(
            user=current_user,
            account_id=account_id,
            days=days,
        )
    except AnalyticsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return AudienceTrendResponse(
        points=[
            AudienceHealthSnapshotResponse.model_validate(point)
            for point in result.points
        ],
        positive_change=result.positive_change,
        negative_change=result.negative_change,
        shielded_change=result.shielded_change,
    )
