"""
Camera view component with advanced monitoring features.
"""
import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from typing import Dict, Optional, Any, List, Tuple
from PIL import Image, ImageTk
import asyncio
from datetime import datetime
import time

from ..core.recognition import FaceRecognitionSystem
from ..core.security import ThreatDetector, AntiSpoofingSystem
from ..utils.config import get_settings
from ..utils.logging import get_logger

class CameraView(ttk.Frame):
    """
    Advanced camera view with real-time monitoring and controls
    """
    
    def __init__(self,
                 parent: Any,
                 camera_id: str,
                 camera_config: Dict,
                 recognition_system: FaceRecognitionSystem,
                 threat_detector: ThreatDetector,
                 anti_spoofing: AntiSpoofingSystem):
        super().__init__(parent)
        
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        self.camera_id = camera_id
        self.camera_config = camera_config
        self.recognition_system = recognition_system
        self.threat_detector = threat_detector
        self.anti_spoofing = anti_spoofing
        
        # Initialize camera
        self.capture = self._init_camera()
        
        # Initialize UI
        self._create_layout()
        
        # Initialize processing flags
        self.enable_recognition = True
        self.enable_threat_detection = True
        self.enable_recording = True
        self.show_debug = False
        
        # Initialize statistics
        self.stats = {
            "fps": 0,
            "faces_detected": 0,
            "threats_detected": 0,
            "processing_time": 0
        }
        
        # Initialize frame buffer for motion detection
        self.frame_buffer = []
        self.max_buffer_size = 30
        
        # Start processing
        self.running = True
        self.frame_count = 0
        
    def _init_camera(self) -> cv2.VideoCapture:
        """Initialize camera capture"""
        try:
            if self.camera_config["type"] == "usb":
                cap = cv2.VideoCapture(self.camera_config["device_id"])
            elif self.camera_config["type"] == "ip":
                cap = cv2.VideoCapture(self.camera_config["url"])
            else:
                raise ValueError(f"Unknown camera type: {self.camera_config['type']}")
                
            # Configure camera settings
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)
            cap.set(cv2.CAP_PROP_FPS, self.settings.camera_fps)
            
            if not cap.isOpened():
                raise ValueError(f"Failed to open camera {self.camera_id}")
                
            return cap
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {str(e)}")
            raise
            
    def _create_layout(self):
        """Create camera view layout"""
        # Create main display
        self.display_frame = ttk.Frame(self)
        self.display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create camera feed display
        self.feed_label = ttk.Label(self.display_frame)
        self.feed_label.pack(fill=tk.BOTH, expand=True)
        
        # Create control panel
        self.control_panel = ttk.Frame(self)
        self.control_panel.pack(fill=tk.X)
        
        # Add controls
        self._add_controls()
        
        # Create status bar
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(fill=tk.X)
        
        # Add status labels
        self.fps_label = ttk.Label(
            self.status_bar,
            text="FPS: 0",
            style="Status.TLabel"
        )
        self.fps_label.pack(side=tk.LEFT, padx=5)
        
        self.face_count_label = ttk.Label(
            self.status_bar,
            text="Faces: 0",
            style="Status.TLabel"
        )
        self.face_count_label.pack(side=tk.LEFT, padx=5)
        
        self.threat_label = ttk.Label(
            self.status_bar,
            text="Threats: 0",
            style="Status.TLabel"
        )
        self.threat_label.pack(side=tk.LEFT, padx=5)
        
    def _add_controls(self):
        """Add camera controls"""
        # Add toggle buttons
        self.recognition_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.control_panel,
            text="Recognition",
            variable=self.recognition_var,
            command=self._toggle_recognition
        ).pack(side=tk.LEFT, padx=5)
        
        self.threat_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.control_panel,
            text="Threat Detection",
            variable=self.threat_var,
            command=self._toggle_threat_detection
        ).pack(side=tk.LEFT, padx=5)
        
        self.recording_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.control_panel,
            text="Recording",
            variable=self.recording_var,
            command=self._toggle_recording
        ).pack(side=tk.LEFT, padx=5)
        
        self.debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.control_panel,
            text="Debug Info",
            variable=self.debug_var,
            command=self._toggle_debug
        ).pack(side=tk.LEFT, padx=5)
        
        # Add snapshot button
        ttk.Button(
            self.control_panel,
            text="Snapshot",
            command=self._take_snapshot
        ).pack(side=tk.RIGHT, padx=5)
        
    async def process_frame(self) -> Optional[np.ndarray]:
        """Process single camera frame"""
        try:
            start_time = time.time()
            
            # Read frame
            ret, frame = self.capture.read()
            if not ret:
                return None
                
            self.frame_count += 1
            
            # Update frame buffer
            self.frame_buffer.append(frame)
            if len(self.frame_buffer) > self.max_buffer_size:
                self.frame_buffer.pop(0)
                
            # Process frame
            processed_frame = frame.copy()
            
            # Face recognition
            if self.enable_recognition:
                processed_frame = await self._process_recognition(processed_frame)
                
            # Threat detection
            if self.enable_threat_detection:
                processed_frame = await self._process_threats(processed_frame)
                
            # Add debug information
            if self.show_debug:
                processed_frame = self._add_debug_info(processed_frame)
                
            # Update statistics
            self.stats["processing_time"] = time.time() - start_time
            self.stats["fps"] = 1.0 / self.stats["processing_time"]
            
            # Update status
            self._update_status()
            
            return processed_frame
            
        except Exception as e:
            self.logger.error(f"Frame processing failed: {str(e)}")
            return None
            
    async def _process_recognition(self,
                                 frame: np.ndarray) -> np.ndarray:
        """Process face recognition"""
        try:
            # Detect faces
            faces = await self.recognition_system.detect_faces(frame)
            self.stats["faces_detected"] = len(faces)
            
            # Process each face
            for face in faces:
                # Check liveness if enabled
                if self.settings.enable_anti_spoofing:
                    liveness = await self.anti_spoofing.check_liveness(
                        frame,
                        face.bbox,
                        face.landmarks
                    )
                    
                    if liveness.overall_score < self.settings.liveness_threshold:
                        self._draw_spoof_alert(frame, face.bbox)
                        continue
                        
                # Identify face
                matches = await self.recognition_system.identify_face(
                    frame,
                    face
                )
                
                # Draw results
                self._draw_face_results(frame, face, matches)
                
            return frame
            
        except Exception as e:
            self.logger.error(f"Recognition processing failed: {str(e)}")
            return frame
            
    async def _process_threats(self,
                             frame: np.ndarray) -> np.ndarray:
        """Process threat detection"""
        try:
            # Detect threats
            threats = await self.threat_detector.detect_threats(
                frame,
                self.frame_count,
                self.frame_buffer
            )
            
            self.stats["threats_detected"] = len(threats)
            
            # Draw threats
            for threat in threats:
                self._draw_threat(frame, threat)
                
            return frame
            
        except Exception as e:
            self.logger.error(f"Threat processing failed: {str(e)}")
            return frame
            
    def _draw_face_results(self,
                          frame: np.ndarray,
                          face: Any,
                          matches: List[Any]):
        """Draw face detection and recognition results"""
        try:
            x1, y1, x2, y2 = face.bbox
            
            if matches:
                # Known face
                match = matches[0]
                color = (0, 255, 0)  # Green
                name = match.person_id
                conf = f"{match.confidence:.2f}"
            else:
                # Unknown face
                color = (0, 0, 255)  # Red
                name = "Unknown"
                conf = "N/A"
                
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{name} ({conf})"
            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )
            
        except Exception as e:
            self.logger.error(f"Drawing error: {str(e)}")
            
    def _draw_spoof_alert(self,
                         frame: np.ndarray,
                         bbox: Tuple[int, int, int, int]):
        """Draw spoof detection alert"""
        try:
            x1, y1, x2, y2 = bbox
            
            # Draw red box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Draw warning
            cv2.putText(
                frame,
                "SPOOF DETECTED",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2
            )
            
        except Exception as e:
            self.logger.error(f"Drawing error: {str(e)}")
            
    def _draw_threat(self, frame: np.ndarray, threat: Any):
        """Draw threat detection results"""
        try:
            # Draw threat box
            cv2.rectangle(
                frame,
                (threat.location[0], threat.location[1]),
                (threat.location[2], threat.location[3]),
                (0, 0, 255),
                2
            )
            
            # Draw threat label
            label = f"{threat.event_type} ({threat.confidence:.2f})"
            cv2.putText(
                frame,
                label,
                (threat.location[0], threat.location[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2
            )
            
        except Exception as e:
            self.logger.error(f"Drawing error: {str(e)}")
            
    def _add_debug_info(self, frame: np.ndarray) -> np.ndarray:
        """Add debug information to frame"""
        try:
            # Add processing statistics
            cv2.putText(
                frame,
                f"FPS: {self.stats['fps']:.1f}",
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            
            cv2.putText(
                frame,
                f"Processing: {self.stats['processing_time']*1000:.1f}ms",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            
            # Add camera info
            cv2.putText(
                frame,
                f"Camera: {self.camera_id}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Debug info error: {str(e)}")
            return frame
            
    def _update_status(self):
        """Update status bar information"""
        try:
            self.fps_label.config(
                text=f"FPS: {self.stats['fps']:.1f}"
            )
            self.face_count_label.config(
                text=f"Faces: {self.stats['faces_detected']}"
            )
            self.threat_label.config(
                text=f"Threats: {self.stats['threats_detected']}"
            )
        except Exception as e:
            self.logger.error(f"Status update error: {str(e)}")
            
    def _take_snapshot(self):
        """Save current frame as snapshot"""
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshots/{self.camera_id}_{timestamp}.jpg"
            
            # Save frame
            ret, frame = self.capture.read()
            if ret:
                cv2.imwrite(filename, frame)
                self.logger.info(f"Snapshot saved: {filename}")
                
        except Exception as e:
            self.logger.error(f"Snapshot error: {str(e)}")
            
    def _toggle_recognition(self):
        """Toggle face recognition"""
        self.enable_recognition = self.recognition_var.get()
        
    def _toggle_threat_detection(self):
        """Toggle threat detection"""
        self.enable_threat_detection = self.threat_var.get()
        
    def _toggle_recording(self):
        """Toggle video recording"""
        self.enable_recording = self.recording_var.get()
        
    def _toggle_debug(self):
        """Toggle debug information"""
        self.show_debug = self.debug_var.get()
        
    async def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.capture is not None:
            self.capture.release() 