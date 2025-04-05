import cv2
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os
from typing import Optional, Tuple
import logging

from .utils.timestamp_overlay import add_timestamp_overlay
from .utils.file_loader import VideoFile

logger = logging.getLogger(__name__)

class VideoPlayer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Video Review System")
        
        # Video state
        self.current_video: Optional[VideoFile] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        
        # GUI elements
        self.setup_gui()
        
        # Video display
        self.video_label = ttk.Label(root)
        self.video_label.pack(pady=10)
        
        # Controls
        self.setup_controls()
        
    def setup_gui(self):
        """Set up the main GUI elements."""
        # Video info frame
        info_frame = ttk.LabelFrame(self.root, text="Video Information")
        info_frame.pack(fill="x", padx=5, pady=5)
        
        self.info_label = ttk.Label(info_frame, text="No video loaded")
        self.info_label.pack(pady=5)
        
        # Timeline frame
        timeline_frame = ttk.LabelFrame(self.root, text="Timeline")
        timeline_frame.pack(fill="x", padx=5, pady=5)
        
        self.timeline = ttk.Scale(
            timeline_frame,
            from_=0,
            to=100,
            orient="horizontal",
            command=self.on_timeline_change
        )
        self.timeline.pack(fill="x", padx=5, pady=5)
        
        self.time_label = ttk.Label(timeline_frame, text="00:00:00 / 00:00:00")
        self.time_label.pack(pady=5)
        
    def setup_controls(self):
        """Set up video playback controls."""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # Playback controls
        ttk.Button(control_frame, text="⏮", command=self.rewind).pack(side="left", padx=2)
        ttk.Button(control_frame, text="⏯", command=self.toggle_play).pack(side="left", padx=2)
        ttk.Button(control_frame, text="⏭", command=self.fast_forward).pack(side="left", padx=2)
        
        # Time jump controls
        time_frame = ttk.Frame(control_frame)
        time_frame.pack(side="right", padx=5)
        
        ttk.Label(time_frame, text="Jump to:").pack(side="left")
        self.time_entry = ttk.Entry(time_frame, width=8)
        self.time_entry.pack(side="left", padx=2)
        ttk.Button(time_frame, text="Go", command=self.jump_to_time).pack(side="left")
        
    def load_video(self, video_file: VideoFile):
        """Load a video file for playback."""
        try:
            if self.cap is not None:
                self.cap.release()
                
            self.current_video = video_file
            self.cap = cv2.VideoCapture(video_file.filepath)
            
            if not self.cap.isOpened():
                raise ValueError(f"Could not open video file: {video_file.filepath}")
                
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            self.timeline.configure(to=self.total_frames)
            self.update_info_label()
            self.update_frame()
            
        except Exception as e:
            logger.error(f"Error loading video: {e}")
            self.info_label.config(text=f"Error loading video: {str(e)}")
            
    def update_frame(self):
        """Update the current video frame with timestamp overlay."""
        if self.cap is None or not self.cap.isOpened():
            return
            
        ret, frame = self.cap.read()
        if not ret:
            self.current_frame = 0
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            
        if ret:
            # Add timestamp overlay
            timestamp = self.current_video.timestamp + self.current_frame / self.fps
            frame = add_timestamp_overlay(frame, timestamp)
            
            # Convert frame for display
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (800, 600))
            
            # Update display
            photo = tk.PhotoImage(data=cv2.imencode('.png', frame)[1].tobytes())
            self.video_label.configure(image=photo)
            self.video_label.image = photo
            
            # Update timeline and time label
            self.timeline.set(self.current_frame)
            current_time = self.current_frame / self.fps
            total_time = self.total_frames / self.fps
            self.time_label.config(
                text=f"{self.format_time(current_time)} / {self.format_time(total_time)}"
            )
            
            if self.is_playing:
                self.current_frame += 1
                self.root.after(int(1000/self.fps), self.update_frame)
                
    def toggle_play(self):
        """Toggle video playback."""
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.update_frame()
            
    def rewind(self):
        """Rewind video by 5 seconds."""
        if self.cap is not None:
            self.current_frame = max(0, self.current_frame - int(5 * self.fps))
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            self.update_frame()
            
    def fast_forward(self):
        """Fast forward video by 5 seconds."""
        if self.cap is not None:
            self.current_frame = min(
                self.total_frames,
                self.current_frame + int(5 * self.fps)
            )
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            self.update_frame()
            
    def jump_to_time(self):
        """Jump to a specific time in the video."""
        try:
            time_str = self.time_entry.get()
            hours, minutes, seconds = map(int, time_str.split(':'))
            target_time = hours * 3600 + minutes * 60 + seconds
            
            if self.cap is not None:
                self.current_frame = int(target_time * self.fps)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
                self.update_frame()
                
        except ValueError:
            logger.warning("Invalid time format. Use HH:MM:SS")
            
    def on_timeline_change(self, value):
        """Handle timeline slider changes."""
        if self.cap is not None:
            self.current_frame = int(float(value))
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            self.update_frame()
            
    def update_info_label(self):
        """Update the video information label."""
        if self.current_video:
            info_text = (
                f"File: {os.path.basename(self.current_video.filepath)}\n"
                f"Date: {self.current_video.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Camera: {self.current_video.camera_id}"
            )
            self.info_label.config(text=info_text)
            
    @staticmethod
    def format_time(seconds: float) -> str:
        """Format seconds into HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
    def __del__(self):
        """Clean up resources."""
        if self.cap is not None:
            self.cap.release() 