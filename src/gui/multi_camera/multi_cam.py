from typing import Dict, List
from PyQt5.QtWidgets import QWidget, QGridLayout
from core.camera.manager import CameraManager
from core.resource_pool import ResourcePool
from core.error_handling import handle_exceptions

class MultiCameraView(QWidget):
    def __init__(self):
        super().__init__()
        self.camera_manager = CameraManager()
        self.camera_pool = ResourcePool(
            create_resource=self._create_camera_widget,
            cleanup_resource=self._cleanup_camera_widget
        )
        self.active_views: Dict[int, 'CameraWidget'] = {}
        self.setup_ui()

    @handle_exceptions(logger=multicam_logger.error)
    async def setup_ui(self):
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        await self.initialize_camera_views()

    async def initialize_camera_views(self):
        camera_configs = self.camera_manager.active_streams.items()
        for camera_id, stream in camera_configs:
            with self.camera_pool.acquire() as widget:
                self.active_views[camera_id] = widget
                self._add_camera_to_grid(widget, camera_id)

    def _create_camera_widget(self) -> 'CameraWidget':
        return CameraWidget()

    def _cleanup_camera_widget(self, widget: 'CameraWidget'):
        widget.stop()
        widget.deleteLater()

    def _add_camera_to_grid(self, widget: 'CameraWidget', camera_id: int):
        row = (camera_id - 1) // 2
        col = (camera_id - 1) % 2
        self.layout.addWidget(widget, row, col) 
