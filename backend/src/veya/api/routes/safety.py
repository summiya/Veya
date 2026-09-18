from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from veya.api.dependencies.authentication import get_current_user
from veya.api.schemas.safety import (
    SafetyAnalyzeResponse,
    SafetyCommentResponse,
    SafetySummaryResponse,
)
from veya.application.safety.service import SafetyAnalysisError, SafetyService
from veya.domain.users.models import User
from veya.infrastructure.database.dependencies import get_db


router = APIRouter(prefix="/api/safety", tags=["safety"])


@router.post(
    "/instagram/accounts/{account_id}/analyze",
    response_model=SafetyAnalyzeResponse,
)
def analyze_account_safety(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SafetyAnalyzeResponse:
    try:
        result = SafetyService(db).analyze_account(
            user=current_user,
            account_id=account_id,
        )
    except SafetyAnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return SafetyAnalyzeResponse(analyzed_comments=result.analyzed_comments)


@router.get(
    "/instagram/accounts/{account_id}",
    response_model=SafetySummaryResponse,
)
def account_safety_summary(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SafetySummaryResponse:
    try:
        result = SafetyService(db).account_summary(
            user=current_user,
            account_id=account_id,
        )
    except SafetyAnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return SafetySummaryResponse(**result.__dict__)


@router.get(
    "/instagram/accounts/{account_id}/feed",
    response_model=list[SafetyCommentResponse],
)
def positive_constructive_feed(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[SafetyCommentResponse]:
    try:
        comments = SafetyService(db).positive_and_constructive_comments(
            user=current_user,
            account_id=account_id,
            limit=limit,
        )
    except SafetyAnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [
        SafetyCommentResponse(
            id=comment.id,
            text=comment.text,
            username=comment.username,
            commented_at=comment.commented_at,
        )
        for comment in comments
    ]


@router.get(
    "/instagram/accounts/{account_id}/shielded",
    response_model=list[SafetyCommentResponse],
)
def shielded_comments(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    reveal: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[SafetyCommentResponse]:
    try:
        comments = SafetyService(db).shielded_comments(
            user=current_user,
            account_id=account_id,
            reveal=reveal,
            limit=limit,
        )
    except SafetyAnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [
        SafetyCommentResponse(
            id=comment.id,
            text=comment.text,
            username=comment.username,
            commented_at=comment.commented_at,
        )
        for comment in comments
    ]
