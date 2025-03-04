import os
import sys
import logging
from pathlib import Path
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

def initialize_app():
    """Initialize the application components."""
    try:
        # Import and initialize core components
        from core.database.service import DatabaseService
        from core.face_recognition.service import FaceRecognitionService
        from core.monitoring.system.manager import SystemMonitor
        
        # Initialize services
        db_service = DatabaseService()
        face_service = FaceRecognitionService()
        system_monitor = SystemMonitor()
        
        logger.info("Application components initialized successfully")
        return {
            'db_service': db_service,
            'face_service': face_service,
            'system_monitor': system_monitor
        }
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        sys.exit(1)

def main():
    """Main entry point for the application."""
    try:
        # Set up environment
        setup_environment()
        
        # Initialize application
        services = initialize_app()
        
        # Start system monitoring
        services['system_monitor'].start_monitoring()
        
        logger.info("Application started successfully")
        
        # Keep the application running
        try:
            while True:
                pass
        except KeyboardInterrupt:
            logger.info("Application shutting down...")
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 