from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from veya.api.dependencies.authentication import get_current_user
from veya.api.schemas.insights import AudienceInsightResponse
from veya.application.insights.service import AudienceInsightsError, AudienceInsightsService
from veya.domain.users.models import User
from veya.infrastructure.database.dependencies import get_db


router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.post(
    "/instagram/accounts/{account_id}/generate",
    response_model=AudienceInsightResponse,
)
def generate_audience_insights(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AudienceInsightResponse:
    try:
        insight = AudienceInsightsService(db).generate(
            user=current_user,
            account_id=account_id,
        )
    except AudienceInsightsError as exc:
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "OPENAI_API_KEY" in str(exc) or "generation failed" in str(exc)
            else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return AudienceInsightResponse.model_validate(insight)


@router.get(
    "/instagram/accounts/{account_id}",
    response_model=AudienceInsightResponse | None,
)
def get_audience_insights(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AudienceInsightResponse | None:
    try:
        insight = AudienceInsightsService(db).get_current(
            user=current_user,
            account_id=account_id,
        )
    except AudienceInsightsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if insight is None:
        return None
    return AudienceInsightResponse.model_validate(insight)
