from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QImage, QPixmap, QPainter, QWheelEvent, QMouseEvent
from core.error_handling import handle_exceptions

class CameraFeedWidget(QWidget):
    def __init__(self, camera_id: int):
        super().__init__()
        self.camera_id = camera_id
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.dragging = False
        self.last_pos = None
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.feed_label = QLabel()
        self.feed_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.feed_label)
        
        self.setMouseTracking(True)
        self.feed_label.setMouseTracking(True)

    def wheelEvent(self, event: QWheelEvent):
        # Handle zoom
        zoom_in = event.angleDelta().y() > 0
        if zoom_in and self.zoom_factor < 5.0:
            self.zoom_factor *= 1.1
        elif not zoom_in and self.zoom_factor > 0.5:
            self.zoom_factor /= 1.1
        self.update_view()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_pos = event.pos()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging and self.last_pos:
            delta = event.pos() - self.last_pos
            self.pan_x += delta.x()
            self.pan_y += delta.y()
            self.last_pos = event.pos()
            self.update_view()

    @handle_exceptions(logger=camera_logger.error)
    def update_view(self):
        if hasattr(self, 'current_frame'):
            # Apply zoom and pan transformations
            painter = QPainter(self.current_frame)
            painter.translate(self.pan_x, self.pan_y)
            painter.scale(self.zoom_factor, self.zoom_factor)
            
            # Update the display
            self.feed_label.setPixmap(QPixmap.fromImage(self.current_frame)) 
