"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
import numpy as np
import cv2

from core.auth.service import AuthService
from core.auth.schemas import Token, UserCreate, UserRead
from core.auth.dependencies import get_current_user
from core.database.connection import get_db
from core.config import Settings
from core.logging import get_logger
from core.face_recognition.core import FaceRecognitionSystem

router = APIRouter(prefix="/auth", tags=["auth"])
settings = Settings()
logger = get_logger(__name__)
recognition_service = FaceRecognitionSystem()

# Initialize with your face data
MACE_SCOTT_USERNAME = "mace.scott"
MACE_SCOTT_EMAIL = "mace.scott@cernoid.com"

def get_auth_service(db = Depends(get_db)) -> AuthService:
    """Get auth service instance."""
    return AuthService()

@router.post("/face-login", response_model=Token)
async def face_login(
    image: UploadFile = File(...),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login with face recognition."""
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Verify if it's Mace Scott
        result = await recognition_service.verify_face(img, MACE_SCOTT_USERNAME)
        if result and result.confidence > 0.9:  # High confidence threshold
            # Create access token
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

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login endpoint."""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserRead)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register new user."""
    return await auth_service.create_user(user_data)

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: UserRead = Depends(get_current_user)):
    """Get current user info."""
    return current_user 