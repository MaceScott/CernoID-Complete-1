import tkinter as tk
from tkinter import ttk
import tkcalendar
from datetime import datetime, timedelta
import logging
from typing import Optional, List

from .utils.file_loader import VideoIndex, VideoFile
from .video_player import VideoPlayer

logger = logging.getLogger(__name__)

class VideoBrowserGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Video Review System")
        
        # Initialize components
        self.video_index = VideoIndex()
        self.video_player = VideoPlayer(root)
        
        # Create main layout
        self.create_layout()
        
        # Load initial data
        self.load_videos()
        
    def create_layout(self):
        """Create the main GUI layout."""
        # Create main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for filters
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)
        
        # Right panel for video player
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=3)
        
        # Add video player to right panel
        self.video_player.root.pack(fill=tk.BOTH, expand=True)
        
        # Create filter controls
        self.create_filter_controls(left_panel)
        
        # Create video list
        self.create_video_list(left_panel)
        
    def create_filter_controls(self, parent: ttk.Frame):
        """Create the filter control panel."""
        # Date filter frame
        date_frame = ttk.LabelFrame(parent, text="Date Filter")
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Start date
        ttk.Label(date_frame, text="Start Date:").pack(pady=2)
        self.start_date = tkcalendar.DateEntry(
            date_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2
        )
        self.start_date.pack(pady=2)
        
        # End date
        ttk.Label(date_frame, text="End Date:").pack(pady=2)
        self.end_date = tkcalendar.DateEntry(
            date_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2
        )
        self.end_date.pack(pady=2)
        
        # Camera filter
        camera_frame = ttk.LabelFrame(parent, text="Camera Filter")
        camera_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.camera_var = tk.StringVar()
        self.camera_combo = ttk.Combobox(
            camera_frame,
            textvariable=self.camera_var,
            state="readonly"
        )
        self.camera_combo.pack(fill=tk.X, padx=5, pady=5)
        
        # Person filter
        person_frame = ttk.LabelFrame(parent, text="Person Filter")
        person_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.person_var = tk.StringVar()
        self.person_combo = ttk.Combobox(
            person_frame,
            textvariable=self.person_var,
            state="readonly"
        )
        self.person_combo.pack(fill=tk.X, padx=5, pady=5)
        
        # Incident filter
        self.incident_var = tk.BooleanVar()
        ttk.Checkbutton(
            parent,
            text="Show Incidents Only",
            variable=self.incident_var,
            command=self.apply_filters
        ).pack(pady=5)
        
        # Apply filters button
        ttk.Button(
            parent,
            text="Apply Filters",
            command=self.apply_filters
        ).pack(pady=5)
        
    def create_video_list(self, parent: ttk.Frame):
        """Create the video list display."""
        # Video list frame
        list_frame = ttk.LabelFrame(parent, text="Available Videos")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview
        columns = ("Date", "Time", "Camera", "Persons", "Incident")
        self.video_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings"
        )
        
        # Configure columns
        for col in columns:
            self.video_tree.heading(col, text=col)
            self.video_tree.column(col, width=100)
            
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.video_tree.yview
        )
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.video_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.video_tree.bind("<<TreeviewSelect>>", self.on_video_select)
        
    def load_videos(self):
        """Load videos from the index and update the display."""
        try:
            # Update camera and person lists
            cameras = set()
            persons = set()
            
            for video in self.video_index.videos:
                cameras.add(video.camera_id)
                persons.update(video.detected_persons)
                
            self.camera_combo['values'] = sorted(list(cameras))
            self.person_combo['values'] = sorted(list(persons))
            
            # Apply current filters
            self.apply_filters()
            
        except Exception as e:
            logger.error(f"Error loading videos: {e}")
            
    def apply_filters(self):
        """Apply the current filters and update the video list."""
        try:
            # Clear current list
            for item in self.video_tree.get_children():
                self.video_tree.delete(item)
                
            # Get filter values
            start_date = self.start_date.get_date()
            end_date = self.end_date.get_date()
            camera = self.camera_var.get()
            person = self.person_var.get()
            incidents_only = self.incident_var.get()
            
            # Get filtered videos
            videos = self.video_index.get_videos_by_date(
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.max.time())
            )
            
            if camera:
                videos = [v for v in videos if v.camera_id == camera]
                
            if person:
                videos = [v for v in videos if person in v.detected_persons]
                
            if incidents_only:
                videos = [v for v in videos if v.incident_flag]
                
            # Update treeview
            for video in videos:
                self.video_tree.insert(
                    "",
                    tk.END,
                    values=(
                        video.timestamp.strftime("%Y-%m-%d"),
                        video.timestamp.strftime("%H:%M:%S"),
                        video.camera_id,
                        ", ".join(video.detected_persons),
                        "Yes" if video.incident_flag else "No"
                    ),
                    tags=(video.filepath,)
                )
                
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            
    def on_video_select(self, event):
        """Handle video selection in the treeview."""
        selection = self.video_tree.selection()
        if not selection:
            return
            
        # Get the video filepath from the item tags
        filepath = self.video_tree.item(selection[0])['tags'][0]
        
        # Find the video in the index
        video = next(
            (v for v in self.video_index.videos if v.filepath == filepath),
            None
        )
        
        if video:
            self.video_player.load_video(video) 