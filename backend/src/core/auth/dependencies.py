"""Authentication dependencies."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from core.config import Settings
from core.database.models.models import User
from .schemas import TokenData

settings = Settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = await User.get_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return user 