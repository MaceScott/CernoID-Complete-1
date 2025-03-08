"""Authentication API endpoints."""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Optional
from ..schemas.auth import TokenResponse, UserCreate, UserResponse
from ...core.auth.service import AuthService
from ...core.database.connection import get_db
from ...core.config.settings import get_settings
from ...utils.logging import get_logger

router = APIRouter(tags=["auth"])
settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
logger = get_logger(__name__)

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Login to get access token."""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )

@router.post("/register", response_model=UserResponse)
async def register_user(
    user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Register a new user."""
    db_user = await auth_service.get_user_by_username(user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    db_user = await auth_service.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return await auth_service.create_user(user) 