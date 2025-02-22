from PyQt5.QtWidgets import QWidget, QGridLayout, QMenu
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, Optional
from core.camera.manager import CameraManager
from core.error_handling import handle_exceptions

class CameraFeedManager(QWidget):
    camera_selected = pyqtSignal(int)  # Signal when camera is selected
    
    def __init__(self):
        super().__init__()
        self.camera_manager = CameraManager()
        self.active_feeds: Dict[int, 'CameraFeedWidget'] = {}
        self.selected_camera: Optional[int] = None
        self.layout_mode = "grid"  # or "single"
        self.setup_ui()

    def setup_ui(self):
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.setup_context_menu()

    def setup_context_menu(self):
        self.context_menu = QMenu(self)
        self.context_menu.addAction("Maximize", self.maximize_feed)
        self.context_menu.addAction("Grid View", self.switch_to_grid)
        self.context_menu.addAction("Settings", self.open_camera_settings)

    @handle_exceptions(logger=camera_logger.error)
    async def initialize_feeds(self):
        camera_configs = self.camera_manager.get_active_cameras()
        for config in camera_configs:
            feed = CameraFeedWidget(config['id'])
            self.active_feeds[config['id']] = feed
            await feed.start()
        self.arrange_feeds()

    def arrange_feeds(self):
        if self.layout_mode == "grid":
            self._arrange_grid()
        else:
            self._show_single(self.selected_camera)

    def _arrange_grid(self):
        # Clear current layout
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        # Arrange feeds in grid
        num_feeds = len(self.active_feeds)
        cols = int(num_feeds ** 0.5)
        rows = (num_feeds + cols - 1) // cols
        
        for idx, (camera_id, feed) in enumerate(self.active_feeds.items()):
            row = idx // cols
            col = idx % cols
            self.grid_layout.addWidget(feed, row, col)
            feed.setMinimumSize(320, 240)

    def _show_single(self, camera_id: Optional[int]):
        if camera_id and camera_id in self.active_feeds:
            for feed in self.active_feeds.values():
                feed.hide()
            self.active_feeds[camera_id].show()
            self.active_feeds[camera_id].setMinimumSize(800, 600) 
