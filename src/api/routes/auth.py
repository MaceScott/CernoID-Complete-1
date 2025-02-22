from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict
from core.auth.manager import AuthManager
from core.database.models import User
from .schemas import TokenResponse, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_manager: AuthManager = Depends()
):
    """User login endpoint"""
    user = await auth_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = auth_manager.create_access_token({"sub": user.email})
    refresh_token = auth_manager.create_refresh_token({"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, auth_manager: AuthManager = Depends()):
    """User registration endpoint"""
    try:
        hashed_password = auth_manager.get_password_hash(user_data.password)
        user = await User.create(
            email=user_data.email,
            password_hash=hashed_password,
            name=user_data.name
        )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    auth_manager: AuthManager = Depends()
):
    """Refresh access token"""
    payload = auth_manager.verify_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    access_token = auth_manager.create_access_token({"sub": payload["sub"]})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    } 