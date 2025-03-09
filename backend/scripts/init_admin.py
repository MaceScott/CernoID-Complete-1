"""Initialize admin user with face data."""
import asyncio
import os
from pathlib import Path
import cv2
import numpy as np
from datetime import datetime

from core.auth.service import AuthService
from core.database.connection import db_pool
from core.face_recognition.core import FaceRecognitionSystem
from core.config import Settings

# Admin user data
ADMIN_DATA = {
    "username": "mace.scott",
    "email": "mace.scott@cernoid.com",
    "password": "admin123",  # Change this to a secure password
    "is_active": True,
    "is_admin": True
}

async def init_admin():
    """Initialize admin user with face data."""
    try:
        # Initialize services
        settings = Settings()
        auth_service = AuthService()
        face_service = FaceRecognitionSystem()
        
        # Connect to database
        await db_pool.create_pool()
        
        # Create admin user if not exists
        user = await auth_service.create_user(ADMIN_DATA)
        print(f"Admin user created: {user.username}")
        
        # Load and process admin face image
        face_image_path = Path(__file__).parent / "admin_face.jpg"
        if not face_image_path.exists():
            print(f"Admin face image not found at: {face_image_path}")
            return
        
        # Read and process face image
        img = cv2.imread(str(face_image_path))
        if img is None:
            print("Failed to read admin face image")
            return
        
        # Register face
        result = await face_service.register_face(img, user.id)
        if result:
            print("Admin face registered successfully")
        else:
            print("Failed to register admin face")
            
    except Exception as e:
        print(f"Error initializing admin: {e}")
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(init_admin()) 