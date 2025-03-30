"""Mock dlib module."""
from unittest.mock import MagicMock
from weakref import WeakValueDictionary

class MockRectangle:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

class MockShapePredictor:
    def __init__(self):
        self.predict = MagicMock(return_value=MagicMock())
        self.__call__ = self.predict

class MockFaceDetector:
    def __init__(self):
        self.detect = MagicMock(return_value=[MockRectangle(0, 0, 100, 100)])
        self.__call__ = self.detect

class MockFaceRecognitionModel:
    def __init__(self):
        self.compute_face_descriptor = MagicMock(return_value=[0.0] * 128)
        self.__call__ = self.compute_face_descriptor

class MockDlib:
    def __init__(self):
        # Use weak references to prevent memory leaks
        self._face_detector = MockFaceDetector()
        self._shape_predictor = MockShapePredictor()
        self._face_recognition_model = MockFaceRecognitionModel()
        self.rectangle = MockRectangle(0, 0, 100, 100)
        self.face_recognition_model_v1 = MagicMock()
        self.cnn_face_detection_model_v1 = MagicMock()
        self.mmod_rectangle = MockRectangle
        self.vector = MagicMock(return_value=[0.0] * 128)  # Mock face descriptor
        self.face_distance = MagicMock(return_value=0.0)
        self.face_distance_model = MagicMock()

    def get_frontal_face_detector(self):
        return self._face_detector

    def shape_predictor(self, model_path):
        return self._shape_predictor

    def face_recognition_model_v1(self, model_path):
        return self._face_recognition_model

    def face_distance(self, face1, face2):
        return 0.0

    def face_distance_model(self, face1, face2):
        return 0.0

# Create a global instance
mock_dlib = MockDlib()

# Patch the dlib module
import sys
sys.modules['dlib'] = mock_dlib 