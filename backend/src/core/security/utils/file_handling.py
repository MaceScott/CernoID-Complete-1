import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple
from contextlib import contextmanager
import aiofiles
import magic
from .path_validation import validate_path, PathValidationError

logger = logging.getLogger(__name__)

class FileHandlingError(Exception):
    """Raised when file operations fail"""
    pass

@contextmanager
def safe_open_file(
    file_path: str,
    mode: str = 'r',
    base_dir: Optional[str] = None
):
    """
    Safely open a file with proper validation and error handling.
    
    Args:
        file_path: Path to the file
        mode: File open mode
        base_dir: Base directory to restrict paths to
        
    Yields:
        File object
        
    Raises:
        FileHandlingError: If file operations fail
    """
    try:
        # Validate path
        path = validate_path(file_path, base_dir)
        
        # Check file exists for read operations
        if 'r' in mode and not path.exists():
            raise FileHandlingError(f"File not found: {file_path}")
        
        # Open file
        with open(path, mode) as f:
            yield f
            
    except Exception as e:
        logger.error(f"File operation error: {str(e)}")
        raise FileHandlingError(f"File operation failed: {str(e)}")

async def safe_read_file(
    file_path: str,
    base_dir: Optional[str] = None
) -> bytes:
    """
    Safely read a file asynchronously.
    
    Args:
        file_path: Path to the file
        base_dir: Base directory to restrict paths to
        
    Returns:
        bytes: File contents
        
    Raises:
        FileHandlingError: If file operations fail
    """
    try:
        # Validate path
        path = validate_path(file_path, base_dir)
        
        # Read file
        async with aiofiles.open(path, 'rb') as f:
            return await f.read()
            
    except Exception as e:
        logger.error(f"File read error: {str(e)}")
        raise FileHandlingError(f"File read failed: {str(e)}")

async def safe_write_file(
    file_path: str,
    content: bytes,
    base_dir: Optional[str] = None
) -> None:
    """
    Safely write to a file asynchronously.
    
    Args:
        file_path: Path to the file
        content: Content to write
        base_dir: Base directory to restrict paths to
        
    Raises:
        FileHandlingError: If file operations fail
    """
    try:
        # Validate path
        path = validate_path(file_path, base_dir)
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        async with aiofiles.open(path, 'wb') as f:
            await f.write(content)
            
    except Exception as e:
        logger.error(f"File write error: {str(e)}")
        raise FileHandlingError(f"File write failed: {str(e)}")

def get_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: File hash
        
    Raises:
        FileHandlingError: If file operations fail
    """
    try:
        with safe_open_file(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        logger.error(f"File hash calculation error: {str(e)}")
        raise FileHandlingError(f"File hash calculation failed: {str(e)}")

def validate_file_type(
    file_path: str,
    allowed_types: list[str]
) -> Tuple[bool, str]:
    """
    Validate file type using python-magic.
    
    Args:
        file_path: Path to the file
        allowed_types: List of allowed MIME types
        
    Returns:
        tuple: (is_valid, mime_type)
        
    Raises:
        FileHandlingError: If file operations fail
    """
    try:
        with safe_open_file(file_path, 'rb') as f:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(f.read(2048))
            return mime_type in allowed_types, mime_type
    except Exception as e:
        logger.error(f"File type validation error: {str(e)}")
        raise FileHandlingError(f"File type validation failed: {str(e)}")

def safe_delete_file(file_path: str) -> None:
    """
    Safely delete a file.
    
    Args:
        file_path: Path to the file
        
    Raises:
        FileHandlingError: If file operations fail
    """
    try:
        path = validate_path(file_path)
        if path.exists():
            path.unlink()
    except Exception as e:
        logger.error(f"File deletion error: {str(e)}")
        raise FileHandlingError(f"File deletion failed: {str(e)}") 