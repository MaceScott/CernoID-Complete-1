import pytest
from datetime import datetime, timedelta
import os
import tempfile
from pathlib import Path

from src.video_review.video_browser_gui import VideoBrowserGUI
from src.video_review.incident_logger import IncidentLogger, Incident
from src.video_review.utils.file_loader import VideoIndex, VideoFile

@pytest.fixture
def temp_video_dir():
    """Create a temporary directory for test videos."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a directory structure for videos
        date_dir = os.path.join(temp_dir, "2024-03-20")
        os.makedirs(date_dir)
        
        # Create dummy video files
        video_files = [
            ("CAM1_10-00-00.mp4", "CAM1", ["P1", "P2"]),
            ("CAM1_11-00-00.mp4", "CAM1", ["P2", "P3"]),
            ("CAM2_10-00-00.mp4", "CAM2", ["P1", "P3"]),
            ("CAM2_11-00-00.mp4", "CAM2", ["P2"])
        ]
        
        for filename, camera_id, persons in video_files:
            filepath = os.path.join(date_dir, filename)
            with open(filepath, 'w') as f:
                f.write("dummy video content")
                
        yield temp_dir

@pytest.fixture
def test_video_index(temp_video_dir):
    """Create a test video index with real file paths."""
    index = VideoIndex()
    index.scan_directory(temp_video_dir)
    return index

@pytest.fixture
def test_incident_file(tmp_path):
    """Create a temporary incident file."""
    return str(tmp_path / "test_incidents.json")

@pytest.fixture
def incident_logger(test_video_index, test_incident_file):
    """Create a test incident logger."""
    return IncidentLogger(test_video_index, test_incident_file)

def test_file_loader_integration(temp_video_dir):
    """Test file loader integration with video index."""
    # Create video index
    index = VideoIndex()
    index.scan_directory(temp_video_dir)
    
    # Verify videos were loaded
    assert len(index.videos) > 0
    
    # Test video filtering
    cam1_videos = index.get_videos_by_camera("CAM1")
    assert len(cam1_videos) > 0
    assert all(v.camera_id == "CAM1" for v in cam1_videos)
    
    # Test person filtering
    p1_videos = index.get_videos_by_person("P1")
    assert len(p1_videos) > 0
    assert all("P1" in v.detected_persons for v in p1_videos)
    
    # Test date filtering
    today = datetime.now().date()
    today_videos = index.get_videos_by_date(
        start_date=datetime.combine(today, datetime.min.time()),
        end_date=datetime.combine(today, datetime.max.time())
    )
    assert len(today_videos) > 0

def test_incident_logger_integration(incident_logger, test_video_index):
    """Test incident logger integration with video index."""
    # Add multiple incidents
    incidents = []
    for video in test_video_index.videos[:2]:
        incident = incident_logger.add_incident(
            video_filepath=video.filepath,
            description=f"Test incident for {video.camera_id}",
            severity="High"
        )
        incidents.append(incident)
    
    # Verify incidents were created
    assert len(incident_logger.incidents) == 2
    
    # Test incident filtering
    cam1_incidents = [
        inc for inc in incident_logger.incidents
        if any(v.filepath == inc.video_filepath and v.camera_id == "CAM1"
               for v in test_video_index.videos)
    ]
    assert len(cam1_incidents) > 0
    
    # Test incident resolution
    resolved = incident_logger.resolve_incident(
        incidents[0].id,
        resolution_notes="Resolved test"
    )
    
    assert resolved is not None
    assert resolved.resolved
    
    # Verify unresolved incidents
    unresolved = incident_logger.get_unresolved_incidents()
    assert len(unresolved) == 1
    assert unresolved[0].id == incidents[1].id

# Note: GUI tests are disabled in Docker environment as they require a display
@pytest.mark.skipif(os.environ.get('ENVIRONMENT') == 'production',
                   reason="GUI tests cannot run in Docker container")
def test_video_browser_and_incident_integration(test_video_index, incident_logger):
    """Test integration between video browser and incident logger."""
    pytest.skip("GUI tests cannot run in Docker container")

@pytest.mark.skipif(os.environ.get('ENVIRONMENT') == 'production',
                   reason="GUI tests cannot run in Docker container")
def test_video_player_integration(test_video_index):
    """Test video player integration with video browser."""
    pytest.skip("GUI tests cannot run in Docker container") 