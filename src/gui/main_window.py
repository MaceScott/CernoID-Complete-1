"""
Main GUI window with real-time monitoring and controls.
"""
import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from PIL import Image, ImageTk
from pathlib import Path
import json

from ..core.recognition import FaceRecognitionSystem
from ..core.security import ThreatDetector, AntiSpoofingSystem
from ..core.storage import VideoStorage
from ..utils.config import get_settings
from ..utils.logging import get_logger

class MainWindow:
    """
    Main application window with real-time monitoring
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize systems
        self.recognition_system = FaceRecognitionSystem()
        self.threat_detector = ThreatDetector()
        self.anti_spoofing = AntiSpoofingSystem()
        self.video_storage = VideoStorage()
        
        # Initialize window
        self.root = tk.Tk()
        self.root.title("CernoID Security System")
        self.root.state('zoomed')  # Maximize window
        
        # Load styles
        self._load_styles()
        
        # Create main layout
        self._create_layout()
        
        # Initialize camera sources
        self.cameras = {}
        self.active_cameras = set()
        self._load_cameras()
        
        # Initialize update loop
        self.running = True
        self.update_task = asyncio.create_task(self._update_loop())
        
        # Bind cleanup
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _load_styles(self):
        """Load custom styles and themes"""
        style = ttk.Style()
        
        # Load custom theme if available
        theme_file = Path("assets/theme.json")
        if theme_file.exists():
            with open(theme_file) as f:
                theme = json.load(f)
                
            # Apply theme colors
            for name, config in theme.items():
                style.configure(name, **config)
        else:
            # Default dark theme
            style.configure(".", 
                background="black",
                foreground="white",
                fieldbackground="black"
            )
            
        # Configure specific styles
        style.configure("Alert.TLabel",
            background="red",
            foreground="white",
            font=("Arial", 12, "bold")
        )
        
        style.configure("Status.TLabel",
            background="green",
            foreground="white",
            font=("Arial", 10)
        )
        
    def _create_layout(self):
        """Create main window layout"""
        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create left sidebar
        self.sidebar = ttk.Frame(
            self.main_container,
            width=200,
            style="Sidebar.TFrame"
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # Create camera selection
        self.camera_frame = ttk.LabelFrame(
            self.sidebar,
            text="Cameras",
            style="Sidebar.TLabelframe"
        )
        self.camera_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create alert panel
        self.alert_frame = ttk.LabelFrame(
            self.sidebar,
            text="Alerts",
            style="Sidebar.TLabelframe"
        )
        self.alert_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create status panel
        self.status_frame = ttk.LabelFrame(
            self.sidebar,
            text="System Status",
            style="Sidebar.TLabelframe"
        )
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create main view
        self.main_view = ttk.Frame(self.main_container)
        self.main_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create camera grid
        self.camera_grid = ttk.Frame(self.main_view)
        self.camera_grid.pack(fill=tk.BOTH, expand=True)
        
        # Create control panel
        self.control_panel = ttk.Frame(
            self.main_view,
            style="Control.TFrame"
        )
        self.control_panel.pack(fill=tk.X)
        
        # Add controls
        self._add_controls()
        
    def _add_controls(self):
        """Add control buttons and settings"""
        # Add camera controls
        ttk.Button(
            self.control_panel,
            text="Add Camera",
            command=self._add_camera_dialog
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            self.control_panel,
            text="Remove Camera",
            command=self._remove_camera_dialog
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Add system controls
        ttk.Button(
            self.control_panel,
            text="Settings",
            command=self._open_settings
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        
        ttk.Button(
            self.control_panel,
            text="View Logs",
            command=self._open_logs
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        
    def _load_cameras(self):
        """Load configured cameras"""
        try:
            # Load camera config
            config_file = Path("config/cameras.json")
            if config_file.exists():
                with open(config_file) as f:
                    camera_config = json.load(f)
                    
                # Initialize each camera
                for camera_id, config in camera_config.items():
                    self._add_camera(camera_id, config)
                    
        except Exception as e:
            self.logger.error(f"Failed to load cameras: {str(e)}")
            
    def _add_camera(self, camera_id: str, config: Dict):
        """Add new camera to the system"""
        try:
            # Create camera capture
            if config["type"] == "usb":
                cap = cv2.VideoCapture(config["device_id"])
            elif config["type"] == "ip":
                cap = cv2.VideoCapture(config["url"])
            else:
                raise ValueError(f"Unknown camera type: {config['type']}")
                
            if not cap.isOpened():
                raise ValueError(f"Failed to open camera {camera_id}")
                
            # Create camera frame
            frame = ttk.Frame(
                self.camera_grid,
                style="Camera.TFrame"
            )
            
            # Add camera label
            label = ttk.Label(
                frame,
                text=config["name"],
                style="Camera.TLabel"
            )
            label.pack()
            
            # Add video display
            display = ttk.Label(frame)
            display.pack(fill=tk.BOTH, expand=True)
            
            # Store camera info
            self.cameras[camera_id] = {
                "capture": cap,
                "frame": frame,
                "display": display,
                "config": config
            }
            
            # Update grid layout
            self._update_grid_layout()
            
            # Add to active cameras
            self.active_cameras.add(camera_id)
            
        except Exception as e:
            self.logger.error(f"Failed to add camera {camera_id}: {str(e)}")
            
    def _update_grid_layout(self):
        """Update camera grid layout"""
        # Calculate grid dimensions
        n_cameras = len(self.cameras)
        cols = min(int(np.ceil(np.sqrt(n_cameras))), 3)
        rows = int(np.ceil(n_cameras / cols))
        
        # Place camera frames in grid
        for i, (camera_id, camera) in enumerate(self.cameras.items()):
            row = i // cols
            col = i % cols
            
            camera["frame"].grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=5,
                pady=5
            )
            
        # Configure grid weights
        for i in range(rows):
            self.camera_grid.grid_rowconfigure(i, weight=1)
        for i in range(cols):
            self.camera_grid.grid_columnconfigure(i, weight=1)
            
    async def _update_loop(self):
        """Main update loop for camera processing"""
        while self.running:
            try:
                # Process each active camera
                for camera_id in self.active_cameras:
                    camera = self.cameras[camera_id]
                    
                    # Read frame
                    ret, frame = camera["capture"].read()
                    if not ret:
                        continue
                        
                    # Process frame
                    processed_frame = await self._process_frame(
                        frame,
                        camera_id
                    )
                    
                    # Update display
                    self._update_display(
                        camera["display"],
                        processed_frame
                    )
                    
                # Update every 30ms (approx. 30 FPS)
                await asyncio.sleep(0.03)
                
            except Exception as e:
                self.logger.error(f"Update loop error: {str(e)}")
                await asyncio.sleep(1)
                
    async def _process_frame(self,
                           frame: np.ndarray,
                           camera_id: str) -> np.ndarray:
        """Process camera frame"""
        try:
            # Detect faces
            faces = await self.recognition_system.detect_faces(frame)
            
            # Process each face
            for face in faces:
                # Check liveness
                if self.settings.enable_anti_spoofing:
                    liveness = await self.anti_spoofing.check_liveness(
                        frame,
                        face.bbox,
                        face.landmarks
                    )
                    
                    if liveness.overall_score < self.settings.liveness_threshold:
                        self._add_alert(
                            f"Spoof detected on camera {camera_id}",
                            "high"
                        )
                        continue
                        
                # Recognize face
                matches = await self.recognition_system.identify_face(
                    frame,
                    face
                )
                
                # Draw results
                self._draw_face_results(frame, face, matches)
                
            # Detect threats
            if self.settings.enable_threat_detection:
                threats = await self.threat_detector.detect_threats(
                    frame,
                    self.frame_count,
                    faces
                )
                
                # Process threats
                for threat in threats:
                    self._process_threat(threat, camera_id)
                    
            # Store frame if needed
            if self.settings.enable_recording:
                await self.video_storage.store_frame(
                    frame,
                    camera_id,
                    time.time()
                )
                
            return frame
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")
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
            
    def _process_threat(self, threat: Any, camera_id: str):
        """Process detected threat"""
        try:
            # Add alert
            self._add_alert(
                f"{threat.event_type} on camera {camera_id}",
                "high"
            )
            
            # Trigger alarm if configured
            if self.settings.enable_alarms:
                self._trigger_alarm(threat)
                
        except Exception as e:
            self.logger.error(f"Threat processing error: {str(e)}")
            
    def _update_display(self, display: ttk.Label, frame: np.ndarray):
        """Update camera display"""
        try:
            # Convert frame to PhotoImage
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            photo = ImageTk.PhotoImage(image)
            
            # Update display
            display.configure(image=photo)
            display.image = photo  # Keep reference
            
        except Exception as e:
            self.logger.error(f"Display update error: {str(e)}")
            
    def _add_alert(self, message: str, level: str = "info"):
        """Add new alert to panel"""
        try:
            # Create alert label
            label = ttk.Label(
                self.alert_frame,
                text=f"{datetime.now().strftime('%H:%M:%S')}: {message}",
                style=f"Alert.TLabel"
            )
            label.pack(fill=tk.X, padx=5, pady=2)
            
            # Remove old alerts
            if len(self.alert_frame.winfo_children()) > 10:
                self.alert_frame.winfo_children()[0].destroy()
                
        except Exception as e:
            self.logger.error(f"Alert creation error: {str(e)}")
            
    def _trigger_alarm(self, threat: Any):
        """Trigger security alarm"""
        # Implementation depends on hardware setup
        pass
        
    def _add_camera_dialog(self):
        """Show dialog to add new camera"""
        # Implementation of camera addition dialog
        pass
        
    def _remove_camera_dialog(self):
        """Show dialog to remove camera"""
        # Implementation of camera removal dialog
        pass
        
    def _open_settings(self):
        """Open settings window"""
        # Implementation of settings dialog
        pass
        
    def _open_logs(self):
        """Open log viewer"""
        # Implementation of log viewer
        pass
        
    def _on_closing(self):
        """Clean up resources on window close"""
        self.running = False
        
        # Release cameras
        for camera in self.cameras.values():
            camera["capture"].release()
            
        # Cleanup systems
        asyncio.create_task(self.recognition_system.cleanup())
        asyncio.create_task(self.anti_spoofing.cleanup())
        asyncio.create_task(self.video_storage.cleanup())
        
        self.root.destroy()
        
    def run(self):
        """Start the application"""
        self.root.mainloop() 