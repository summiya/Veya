from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from veya.api.dependencies.authentication import get_current_user
from veya.api.schemas.sentiment import AnalyzeSentimentResponse, SentimentSummaryResponse
from veya.application.sentiment.service import SentimentAnalysisError, SentimentService
from veya.domain.users.models import User
from veya.infrastructure.database.dependencies import get_db


router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


@router.post(
    "/instagram/accounts/{account_id}/analyze",
    response_model=AnalyzeSentimentResponse,
)
def analyze_instagram_account(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AnalyzeSentimentResponse:
    try:
        result = SentimentService(db).analyze_account(
            user=current_user,
            account_id=account_id,
        )
    except SentimentAnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return AnalyzeSentimentResponse(analyzed_comments=result.analyzed_comments)


@router.get(
    "/instagram/accounts/{account_id}",
    response_model=SentimentSummaryResponse,
)
def instagram_account_sentiment(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SentimentSummaryResponse:
    try:
        result = SentimentService(db).account_summary(
            user=current_user,
            account_id=account_id,
        )
    except SentimentAnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return SentimentSummaryResponse(**result.__dict__)


@router.get(
    "/instagram/accounts/{account_id}/media/{media_id}",
    response_model=SentimentSummaryResponse,
)
def instagram_media_sentiment(
    account_id: int,
    media_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SentimentSummaryResponse:
    try:
        result = SentimentService(db).media_summary(
            user=current_user,
            account_id=account_id,
            media_id=media_id,
        )
    except SentimentAnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return SentimentSummaryResponse(**result.__dict__)
