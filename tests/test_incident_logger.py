import pytest
from datetime import datetime, timedelta
import os
import json
from pathlib import Path

from video_review.incident_logger import IncidentLogger, Incident
from video_review.utils.file_loader import VideoIndex, VideoFile

@pytest.fixture
def test_video_index():
    """Create a test video index."""
    index = VideoIndex()
    index.videos = [
        VideoFile(
            filepath="test_video1.mp4",
            timestamp=datetime.now(),
            camera_id="CAM1",
            detected_persons=["P1", "P2"],
            incident_flag=False
        ),
        VideoFile(
            filepath="test_video2.mp4",
            timestamp=datetime.now() - timedelta(hours=1),
            camera_id="CAM2",
            detected_persons=["P3"],
            incident_flag=False
        )
    ]
    return index

@pytest.fixture
def test_incident_file(tmp_path):
    """Create a temporary incident file."""
    return str(tmp_path / "test_incidents.json")

@pytest.fixture
def incident_logger(test_video_index, test_incident_file):
    """Create a test incident logger."""
    return IncidentLogger(test_video_index, test_incident_file)

def test_add_incident(incident_logger):
    """Test adding a new incident."""
    incident = incident_logger.add_incident(
        video_filepath="test_video1.mp4",
        description="Test incident",
        severity="High",
        notes="Test notes"
    )
    
    assert incident.id.startswith("INC-")
    assert incident.timestamp is not None
    assert incident.video_filepath == "test_video1.mp4"
    assert incident.description == "Test incident"
    assert incident.severity == "High"
    assert incident.notes == "Test notes"
    assert not incident.resolved
    
    # Check that video was marked with incident
    video = next(v for v in incident_logger.video_index.videos if v.filepath == "test_video1.mp4")
    assert video.incident_flag

def test_resolve_incident(incident_logger):
    """Test resolving an incident."""
    # Add an incident
    incident = incident_logger.add_incident(
        video_filepath="test_video1.mp4",
        description="Test incident",
        severity="High"
    )
    
    # Resolve it
    resolved = incident_logger.resolve_incident(
        incident.id,
        resolution_notes="Resolved test"
    )
    
    assert resolved is not None
    assert resolved.resolved
    assert resolved.resolution_time is not None
    assert resolved.resolution_notes == "Resolved test"

def test_get_incidents_by_date(incident_logger):
    """Test filtering incidents by date."""
    # Add incidents at different times
    now = datetime.now()
    incident_logger.add_incident(
        video_filepath="test_video1.mp4",
        description="Recent incident",
        severity="High"
    )
    
    # Add an older incident
    old_incident = incident_logger.add_incident(
        video_filepath="test_video2.mp4",
        description="Old incident",
        severity="Medium"
    )
    old_incident.timestamp = now - timedelta(days=1)
    
    # Get recent incidents
    recent = incident_logger.get_incidents_by_date(
        start_date=now - timedelta(hours=1)
    )
    assert len(recent) == 1
    assert recent[0].description == "Recent incident"

def test_get_incidents_by_video(incident_logger):
    """Test filtering incidents by video."""
    # Add incidents for different videos
    incident_logger.add_incident(
        video_filepath="test_video1.mp4",
        description="First video incident",
        severity="High"
    )
    incident_logger.add_incident(
        video_filepath="test_video2.mp4",
        description="Second video incident",
        severity="Medium"
    )
    
    # Get incidents for first video
    video1_incidents = incident_logger.get_incidents_by_video("test_video1.mp4")
    assert len(video1_incidents) == 1
    assert video1_incidents[0].description == "First video incident"

def test_get_unresolved_incidents(incident_logger):
    """Test getting unresolved incidents."""
    # Add multiple incidents
    incident_logger.add_incident(
        video_filepath="test_video1.mp4",
        description="First incident",
        severity="High"
    )
    incident_logger.add_incident(
        video_filepath="test_video2.mp4",
        description="Second incident",
        severity="Medium"
    )
    
    # Resolve one incident
    incident_logger.resolve_incident(incident_logger.incidents[0].id)
    
    # Get unresolved incidents
    unresolved = incident_logger.get_unresolved_incidents()
    assert len(unresolved) == 1
    assert unresolved[0].description == "Second incident"

def test_save_and_load_incidents(incident_logger, test_incident_file):
    """Test saving and loading incidents from file."""
    # Add some incidents
    incident_logger.add_incident(
        video_filepath="test_video1.mp4",
        description="Test incident",
        severity="High"
    )
    
    # Create new logger instance
    new_logger = IncidentLogger(incident_logger.video_index, test_incident_file)
    
    # Check that incidents were loaded
    assert len(new_logger.incidents) == 1
    assert new_logger.incidents[0].description == "Test incident"
    assert new_logger.incidents[0].severity == "High"

def test_incident_file_handling(incident_logger, test_incident_file):
    """Test handling of incident file operations."""
    # Test with non-existent file
    incident_logger.load_incidents()
    assert len(incident_logger.incidents) == 0
    
    # Add an incident
    incident_logger.add_incident(
        video_filepath="test_video1.mp4",
        description="Test incident",
        severity="High"
    )
    
    # Verify file was created
    assert os.path.exists(test_incident_file)
    
    # Verify file contents
    with open(test_incident_file, 'r') as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]['description'] == "Test incident"
        assert data[0]['severity'] == "High" 