from typing import Dict
from PyQt5.QtWidgets import QMainWindow
from core.events.manager import EventManager
from core.camera.manager import CameraManager
from core.auth.authenticator import AuthManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.event_manager = EventManager()
        self.camera_manager = CameraManager()
        self.auth_manager = AuthManager()
        self.setup_ui()
        self.initialize_event_handlers()

    async def setup_ui(self):
        self.setWindowTitle("CernoID Security System")
        await self.initialize_camera_feeds()
        self.setup_sidebar()
        self.setup_status_bar()

    async def initialize_camera_feeds(self):
        await self.camera_manager.initialize_cameras(
            self.config.get('cameras', [])
        )
        for stream in self.camera_manager.active_streams.values():
            self.add_camera_feed(stream)

    async def initialize_event_handlers(self):
        await self.event_manager.subscribe(
            'face_verified', 
            self.handle_face_verified
        )
        await self.event_manager.subscribe(
            'face_unverified',
            self.handle_face_unverified
        ) 
