"""Mock dlib module."""
from unittest.mock import MagicMock

class MockRectangle:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

class MockDlib:
    def __init__(self):
        self.get_frontal_face_detector = MagicMock()
        self.shape_predictor = MagicMock()
        self.rectangle = MockRectangle(0, 0, 100, 100)
        self.face_recognition_model_v1 = MagicMock()

    def get_frontal_face_detector(self):
        return MagicMock()

    def shape_predictor(self, model_path):
        return MagicMock()

# Create a global instance
mock_dlib = MockDlib()

# Patch the dlib module
import sys
sys.modules['dlib'] = mock_dlib 