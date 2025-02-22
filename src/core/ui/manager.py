from typing import Dict, Optional, Any, List, Union
import asyncio
import cv2
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from ..base import BaseComponent
from ..utils.errors import handle_errors, UIError

class UIManager(BaseComponent):
    """Real-time facial recognition UI manager"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._window = None
        self._frames: Dict[str, Any] = {}
        self._controls: Dict[str, Any] = {}
        self._active_camera = None
        self._update_interval = self.config.get('ui.update_interval', 33)  # ~30 FPS
        self._display_size = self.config.get('ui.display_size', (800, 600))
        self._show_confidence = self.config.get('ui.show_confidence', True)
        self._show_stats = self.config.get('ui.show_stats', True)
        self._running = False

    async def initialize(self) -> None:
        """Initialize UI manager"""
        try:
            # Create main window
            self._window = tk.Tk()
            self._window.title("CernoID-Complete Security System")
            self._window.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # Create UI layout
            await self._create_layout()
            
            # Start UI update loop
            self._running = True
            asyncio.create_task(self._update_loop())
            
        except Exception as e:
            raise UIError(f"UI initialization failed: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup UI resources"""
        self._running = False
        if self._window:
            self._window.destroy()

    async def _create_layout(self) -> None:
        """Create UI layout"""
        try:
            # Create main container
            container = ttk.Frame(self._window)
            container.pack(fill=tk.BOTH, expand=True)
            
            # Create video frame
            video_frame = ttk.Frame(container)
            video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            self._frames['video'] = ttk.Label(video_frame)
            self._frames['video'].pack(fill=tk.BOTH, expand=True)
            
            # Create sidebar
            sidebar = ttk.Frame(container, width=200)
            sidebar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Camera selection
            camera_frame = ttk.LabelFrame(sidebar, text="Cameras")
            camera_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self._controls['camera_select'] = ttk.Combobox(
                camera_frame,
                state="readonly"
            )
            self._controls['camera_select'].pack(fill=tk.X, padx=5, pady=5)
            self._controls['camera_select'].bind(
                "<<ComboboxSelected>>",
                self._on_camera_select
            )
            
            # System controls
            control_frame = ttk.LabelFrame(sidebar, text="Controls")
            control_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self._controls['process_var'] = tk.BooleanVar(value=True)
            self._controls['process_check'] = ttk.Checkbutton(
                control_frame,
                text="Enable Processing",
                variable=self._controls['process_var'],
                command=self._on_process_toggle
            )
            self._controls['process_check'].pack(fill=tk.X, padx=5, pady=2)
            
            self._controls['record_var'] = tk.BooleanVar(value=False)
            self._controls['record_check'] = ttk.Checkbutton(
                control_frame,
                text="Enable Recording",
                variable=self._controls['record_var'],
                command=self._on_record_toggle
            )
            self._controls['record_check'].pack(fill=tk.X, padx=5, pady=2)
            
            # Statistics display
            stats_frame = ttk.LabelFrame(sidebar, text="Statistics")
            stats_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self._frames['stats'] = ttk.Label(
                stats_frame,
                text="No camera selected",
                justify=tk.LEFT
            )
            self._frames['stats'].pack(fill=tk.X, padx=5, pady=5)
            
            # Alert display
            alert_frame = ttk.LabelFrame(sidebar, text="Alerts")
            alert_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self._frames['alerts'] = tk.Text(
                alert_frame,
                height=5,
                state=tk.DISABLED
            )
            self._frames['alerts'].pack(fill=tk.X, padx=5, pady=5)
            
            # Update camera list
            await self._update_camera_list()
            
        except Exception as e:
            raise UIError(f"Layout creation failed: {str(e)}")

    async def _update_loop(self) -> None:
        """Main UI update loop"""
        while self._running:
            try:
                # Update video frame
                if self._active_camera:
                    frame = await self._active_camera.get_processed_frame()
                    if frame is not None:
                        # Resize frame
                        frame = cv2.resize(
                            frame,
                            self._display_size,
                            interpolation=cv2.INTER_AREA
                        )
                        
                        # Convert to PhotoImage
                        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        image = Image.fromarray(image)
                        photo = ImageTk.PhotoImage(image=image)
                        
                        # Update display
                        self._frames['video'].configure(image=photo)
                        self._frames['video'].image = photo
                        
                        # Update statistics
                        if self._show_stats:
                            await self._update_stats()
                
                # Process UI events
                self._window.update()
                
                # Control update rate
                await asyncio.sleep(self._update_interval / 1000)
                
            except tk.TclError:
                # Window was closed
                break
            except Exception as e:
                self.logger.error(f"UI update error: {str(e)}")
                await asyncio.sleep(1)

    async def _update_camera_list(self) -> None:
        """Update camera selection list"""
        try:
            cameras = list(self.app.vision._cameras.keys())
            self._controls['camera_select']['values'] = cameras
            
            if cameras and not self._active_camera:
                self._controls['camera_select'].set(cameras[0])
                await self._on_camera_select(None)
                
        except Exception as e:
            self.logger.error(f"Camera list update error: {str(e)}")

    async def _update_stats(self) -> None:
        """Update statistics display"""
        try:
            if self._active_camera:
                stats = await self._active_camera.get_stats()
                
                stats_text = (
                    f"FPS: {stats['fps']:.1f}\n"
                    f"Faces Detected: {stats['faces_detected']}\n"
                    f"Frames Processed: {stats['frames_processed']}\n"
                    f"Uptime: {stats['uptime']:.0f}s"
                )
                
                self._frames['stats'].configure(text=stats_text)
                
        except Exception as e:
            self.logger.error(f"Stats update error: {str(e)}")

    async def add_alert(self, message: str) -> None:
        """Add alert message"""
        try:
            self._frames['alerts'].configure(state=tk.NORMAL)
            self._frames['alerts'].insert(
                tk.END,
                f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n"
            )
            self._frames['alerts'].see(tk.END)
            self._frames['alerts'].configure(state=tk.DISABLED)
            
        except Exception as e:
            self.logger.error(f"Alert display error: {str(e)}")

    def _on_closing(self) -> None:
        """Handle window closing"""
        self._running = False
        self._window.quit()

    async def _on_camera_select(self, event) -> None:
        """Handle camera selection"""
        try:
            camera_id = self._controls['camera_select'].get()
            self._active_camera = self.app.vision._cameras.get(camera_id)
            
            if self._active_camera:
                # Update control states
                self._controls['process_var'].set(
                    self._active_camera._processing_enabled
                )
                self._controls['record_var'].set(
                    self._active_camera._recording_enabled
                )
                
        except Exception as e:
            self.logger.error(f"Camera selection error: {str(e)}")

    async def _on_process_toggle(self) -> None:
        """Handle processing toggle"""
        try:
            if self._active_camera:
                if self._controls['process_var'].get():
                    await self._active_camera.enable_processing()
                else:
                    await self._active_camera.disable_processing()
                    
        except Exception as e:
            self.logger.error(f"Processing toggle error: {str(e)}")

    async def _on_record_toggle(self) -> None:
        """Handle recording toggle"""
        try:
            if self._active_camera:
                if self._controls['record_var'].get():
                    await self._active_camera.enable_recording()
                else:
                    await self._active_camera.disable_recording()
                    
        except Exception as e:
            self.logger.error(f"Recording toggle error: {str(e)}") 