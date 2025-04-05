import os
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class VideoFile:
    """Represents a video file with its metadata."""
    filepath: str
    timestamp: datetime
    camera_id: str
    detected_persons: List[str]
    incident_flag: bool = False
    
    @classmethod
    def from_path(cls, filepath: str) -> 'VideoFile':
        """Create a VideoFile instance from a file path."""
        # Extract timestamp from filename
        filename = os.path.basename(filepath)
        try:
            # Expected format: camera_name_HH-MM-SS.mp4
            time_str = filename.split('_')[-1].replace('.mp4', '')
            camera_id = filename.split('_')[0]
            
            # Get date from directory structure
            date_str = os.path.basename(os.path.dirname(filepath))
            
            # Combine date and time
            timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H-%M-%S")
            
            return cls(
                filepath=filepath,
                timestamp=timestamp,
                camera_id=camera_id,
                detected_persons=[],
                incident_flag=False
            )
        except Exception as e:
            logger.error(f"Error parsing video file path: {e}")
            raise ValueError(f"Invalid video file path format: {filepath}")

class VideoIndex:
    """Manages the index of video files and their metadata."""
    
    def __init__(self, index_file: str = "video_index.json"):
        self.index_file = index_file
        self.videos: List[VideoFile] = []
        self.load_index()
        
    def load_index(self):
        """Load the video index from file."""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                    self.videos = [
                        VideoFile(
                            filepath=v['filepath'],
                            timestamp=datetime.fromisoformat(v['timestamp']),
                            camera_id=v['camera_id'],
                            detected_persons=v['detected_persons'],
                            incident_flag=v.get('incident_flag', False)
                        )
                        for v in data
                    ]
        except Exception as e:
            logger.error(f"Error loading video index: {e}")
            self.videos = []
            
    def save_index(self):
        """Save the video index to file."""
        try:
            data = [
                {
                    'filepath': v.filepath,
                    'timestamp': v.timestamp.isoformat(),
                    'camera_id': v.camera_id,
                    'detected_persons': v.detected_persons,
                    'incident_flag': v.incident_flag
                }
                for v in self.videos
            ]
            with open(self.index_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving video index: {e}")
            
    def add_video(self, video: VideoFile):
        """Add a video to the index."""
        self.videos.append(video)
        self.save_index()
        
    def update_video(self, video: VideoFile):
        """Update a video's metadata in the index."""
        for i, v in enumerate(self.videos):
            if v.filepath == video.filepath:
                self.videos[i] = video
                self.save_index()
                return
        self.add_video(video)
        
    def get_videos_by_date(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[VideoFile]:
        """Get videos within a date range."""
        if start_date is None:
            start_date = datetime.min
        if end_date is None:
            end_date = datetime.max
            
        return [
            v for v in self.videos
            if start_date <= v.timestamp <= end_date
        ]
        
    def get_videos_by_person(self, person_name: str) -> List[VideoFile]:
        """Get videos where a specific person was detected."""
        return [
            v for v in self.videos
            if person_name in v.detected_persons
        ]
        
    def get_videos_by_camera(self, camera_id: str) -> List[VideoFile]:
        """Get videos from a specific camera."""
        return [
            v for v in self.videos
            if v.camera_id == camera_id
        ]
        
    def get_incident_videos(self) -> List[VideoFile]:
        """Get videos marked as incidents."""
        return [
            v for v in self.videos
            if v.incident_flag
        ]
        
    def scan_directory(self, base_dir: str):
        """Scan a directory for video files and update the index."""
        try:
            for root, _, files in os.walk(base_dir):
                for file in files:
                    if file.endswith('.mp4'):
                        filepath = os.path.join(root, file)
                        try:
                            video = VideoFile.from_path(filepath)
                            self.update_video(video)
                        except ValueError as e:
                            logger.warning(f"Skipping invalid video file: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            
    def get_video_at_time(
        self,
        timestamp: datetime,
        camera_id: Optional[str] = None
    ) -> Optional[VideoFile]:
        """Get the video file that contains a specific timestamp."""
        for video in self.videos:
            if camera_id and video.camera_id != camera_id:
                continue
                
            # Check if timestamp falls within video duration
            # Note: This assumes videos are continuous and non-overlapping
            if video.timestamp <= timestamp:
                # TODO: Add video duration check once we can get video length
                return video
                
        return None 