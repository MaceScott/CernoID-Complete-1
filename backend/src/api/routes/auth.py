"""
File: auth.py
Purpose: Provides authentication endpoints for the CernoID system.

Key Features:
- Traditional email/password authentication
- Face recognition login
- User registration
- Current user information retrieval
- JWT token management

Dependencies:
- FastAPI: Web framework
- OpenCV: Image processing
- NumPy: Array operations
- Core services:
  - AuthService: Authentication logic
  - FaceRecognitionSystem: Face detection/verification
  - Database connection
  - Logging system

API Endpoints:
- POST /auth/face-login: Face recognition login
- POST /auth/token: Traditional login
- POST /auth/register: User registration
- GET /auth/me: Current user info

Security:
- JWT-based authentication
- Face verification with confidence threshold
- Password hashing (handled by AuthService)
- Rate limiting (handled by middleware)
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
import numpy as np
import cv2
from datetime import timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.service import AuthService
from api.schemas.auth import TokenResponse, UserCreate, UserResponse
from core.auth.dependencies import get_current_user
from core.database import get_db
from core.config.settings import get_settings
from core.logging.base import get_logger
from core.face_recognition.core import FaceRecognitionSystem
from core.database.base import get_session
from core.database.models import User

# Initialize router and services
router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
logger = get_logger(__name__)
recognition_service = FaceRecognitionSystem()

# Hardcoded user for demo purposes
# TODO: Replace with database-driven user management
MACE_SCOTT_USERNAME = "mace.scott"
MACE_SCOTT_EMAIL = "mace.scott@cernoid.com"

def get_auth_service(db = Depends(get_db)) -> AuthService:
    """
    Dependency injection for AuthService.
    
    Args:
        db: Database session (injected by FastAPI)
    
    Returns:
        AuthService: Configured authentication service
    """
    return AuthService()

@router.post("/face-login", response_model=TokenResponse)
async def face_login(
    image: UploadFile = File(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Face recognition login endpoint.
    
    Args:
        image: Uploaded face image file
        auth_service: Injected AuthService instance
    
    Returns:
        TokenResponse: JWT access token and type
    
    Raises:
        HTTPException: If face verification fails or image processing errors occur
    """
    try:
        # Process uploaded image
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Verify face against stored data
        result = await recognition_service.verify_face(img, MACE_SCOTT_USERNAME)
        if result and result.confidence > 0.9:  # High confidence threshold
            # Generate access token
            access_token = auth_service.create_access_token(data={"sub": MACE_SCOTT_USERNAME})
            return {"access_token": access_token, "token_type": "bearer"}
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Face verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Face login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Login endpoint to get access token."""
    auth_service = AuthService(settings)
    user = await auth_service.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    User registration endpoint.
    
    Args:
        user_data: User creation data
        auth_service: Injected AuthService instance
    
    Returns:
        UserResponse: Created user information
    
    Raises:
        HTTPException: If registration fails (e.g., duplicate email)
    """
    return await auth_service.create_user(user_data)

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Injected current user data
    
    Returns:
        UserResponse: Current user information
    
    Raises:
        HTTPException: If user is not authenticated
    """
    return current_user 