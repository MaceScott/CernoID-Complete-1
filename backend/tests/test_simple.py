"""Simple test to verify fixture."""
import pytest

def test_simple(db_session):
    """Test that the fixture works."""
    assert db_session is not None
    result = db_session.execute("SELECT 1")
    assert result.scalar() == 1 