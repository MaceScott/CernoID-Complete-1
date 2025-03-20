"""Minimal test to verify fixture."""
import pytest

def test_minimal(db_session):
    """Test that the fixture works."""
    assert db_session is not None 