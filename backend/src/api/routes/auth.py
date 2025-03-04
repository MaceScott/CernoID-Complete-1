"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Optional
from ..schemas.auth import TokenResponse, UserCreate, UserResponse
from ...core.auth.service import AuthService
from ...core.database.models import User
from ...utils.logging import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
auth_service = AuthService()
logger = get_logger(__name__)

@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint to obtain access token."""
    user = await auth_service.authenticate_user(
        form_data.username,
        form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
        
    token = await auth_service.create_access_token(user)
    return TokenResponse(access_token=token, token_type="bearer")

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register new user."""
    # Implementation 