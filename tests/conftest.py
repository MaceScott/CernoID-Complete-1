import pytest
from datetime import datetime
import os
from pathlib import Path

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    return tmp_path

@pytest.fixture
def test_config():
    """Create test configuration."""
    return {
        "video_dir": "test_videos",
        "incident_file": "incidents.json"
    } 