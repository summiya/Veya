from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from veya.api.dependencies.authentication import get_current_user
from veya.api.schemas.instagram import (
    InstagramAccountResponse,
    InstagramCallbackResponse,
    InstagramConnectResponse,
)
from veya.application.instagram.service import (
    InstagramConnectionError,
    InstagramConnectionService,
)
from veya.domain.users.models import User
from veya.infrastructure.database.dependencies import get_db


router = APIRouter(prefix="/api/integrations/instagram", tags=["instagram"])


@router.get("/connect", response_model=InstagramConnectResponse)
def connect_instagram(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InstagramConnectResponse:
    authorization_url = InstagramConnectionService(db).authorization_url(current_user)
    return InstagramConnectResponse(authorization_url=authorization_url)


@router.get("/callback", response_model=InstagramCallbackResponse)
def instagram_callback(
    code: Annotated[str, Query(min_length=1)],
    state: Annotated[str, Query(min_length=1)],
    db: Annotated[Session, Depends(get_db)],
) -> InstagramCallbackResponse:
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

    return InstagramCallbackResponse(
        account=InstagramAccountResponse.model_validate(result.account)
    )


@router.get("/accounts", response_model=list[InstagramAccountResponse])
def list_instagram_accounts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[InstagramAccountResponse]:
    accounts = InstagramConnectionService(db).list_accounts(current_user)
    return [InstagramAccountResponse.model_validate(account) for account in accounts]
