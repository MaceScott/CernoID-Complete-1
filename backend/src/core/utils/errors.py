"""
Error handling utilities.
"""

import logging

logger = logging.getLogger(__name__)

class MatcherError(Exception):
    """Error raised by the face matcher component."""
    pass 