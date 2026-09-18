from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from veya.api.dependencies.authentication import get_current_user
from veya.api.schemas.authentication import (
    AuthenticationResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from veya.application.authentication.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from veya.application.authentication.service import AuthenticationService
from veya.domain.users.models import User
from veya.infrastructure.database.dependencies import get_db


router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/signup", response_model=AuthenticationResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Annotated[Session, Depends(get_db)]) -> AuthenticationResponse:
    service = AuthenticationService(db)
    try:
        user, tokens = service.signup(email=str(payload.email), password=payload.password)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return AuthenticationResponse(
        user=UserResponse.model_validate(user),
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


@router.post("/login", response_model=AuthenticationResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> AuthenticationResponse:
    service = AuthenticationService(db)
    try:
        user, tokens = service.login(email=str(payload.email), password=payload.password)
    except (InvalidCredentialsError, InactiveUserError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return AuthenticationResponse(
        user=UserResponse.model_validate(user),
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    try:
        tokens = AuthenticationService(db).refresh(payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(payload: LogoutRequest, db: Annotated[Session, Depends(get_db)]) -> MessageResponse:
    AuthenticationService(db).logout(payload.refresh_token)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(current_user)
