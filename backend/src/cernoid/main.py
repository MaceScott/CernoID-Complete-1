"""CernoID Face Recognition System - FastAPI Application"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log')
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Application state
class AppState:
    def __init__(self):
        self.is_ready = False

app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    try:
        # Initialize services
        logger.info("Initializing services...")
        app_state.is_ready = True
        yield
    finally:
        # Cleanup
        logger.info("Shutting down services...")
        app_state.is_ready = False

# Create FastAPI application
app = FastAPI(
    title="CernoID",
    description="Face Recognition Identity Management System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if not app_state.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Application is starting up"
        )
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"}
    )

# Protected route example
@app.get("/protected")
async def protected_route(token: Annotated[str, Depends(oauth2_scheme)]):
    """Example protected route."""
    return JSONResponse(
        status_code=200,
        content={"message": "Access granted"}
    )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    ) 