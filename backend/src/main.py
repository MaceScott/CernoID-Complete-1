import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up environment variables and paths."""
    try:
        # Load environment variables from .env file
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        # Add src directory to Python path
        src_path = Path(__file__).parent
        if str(src_path) not in sys.path:
            sys.path.append(str(src_path))
            
        logger.info("Environment setup completed successfully")
    except Exception as e:
        logger.error(f"Error setting up environment: {e}")
        sys.exit(1)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CernoID API",
        description="Backend API for CernoID facial recognition system",
        version="1.0.0"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and register routers
    from api.routes import auth, users, recognition, monitoring
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(users.router, prefix="/api/users", tags=["Users"])
    app.include_router(recognition.router, prefix="/api/recognition", tags=["Recognition"])
    app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app

# Initialize environment
setup_environment()

# Create FastAPI application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 