import os
from pathlib import Path
from typing import Optional
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class PathValidationError(Exception):
    """Raised when path validation fails"""
    pass

def validate_path(
    path: str,
    base_dir: Optional[str] = None,
    allow_symlinks: bool = False,
    check_permissions: bool = True
) -> Path:
    """
    Validate a file path for security.
    
    Args:
        path: The path to validate
        base_dir: Base directory to restrict paths to
        allow_symlinks: Whether to allow symbolic links
        check_permissions: Whether to check file permissions
        
    Returns:
        Path: The validated path object
        
    Raises:
        PathValidationError: If the path is invalid or unsafe
    """
    try:
        # Convert to Path object
        path_obj = Path(path).resolve()
        
        # Check if path is absolute
        if path_obj.is_absolute():
            if base_dir:
                # Ensure path is within base directory
                base_path = Path(base_dir).resolve()
                if not str(path_obj).startswith(str(base_path)):
                    raise PathValidationError(
                        f"Path {path} is outside base directory {base_dir}"
                    )
            else:
                raise PathValidationError("Absolute paths not allowed")
        
        # Check for symlinks
        if not allow_symlinks and path_obj.is_symlink():
            raise PathValidationError("Symbolic links not allowed")
        
        # Check file permissions
        if check_permissions:
            if path_obj.exists():
                # Check if file is readable
                if not os.access(path_obj, os.R_OK):
                    raise PathValidationError(f"File {path} is not readable")
                
                # Check if file is writable
                if not os.access(path_obj, os.W_OK):
                    raise PathValidationError(f"File {path} is not writable")
        
        return path_obj
        
    except Exception as e:
        logger.error(f"Path validation error: {str(e)}")
        raise PathValidationError(f"Invalid path: {str(e)}")

def validate_url(url: str, allowed_domains: Optional[list] = None) -> bool:
    """
    Validate a URL for security.
    
    Args:
        url: The URL to validate
        allowed_domains: List of allowed domains
        
    Returns:
        bool: True if URL is valid and safe
        
    Raises:
        PathValidationError: If the URL is invalid or unsafe
    """
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ['http', 'https']:
            raise PathValidationError("Only http and https URLs allowed")
        
        # Check domain
        if allowed_domains:
            domain = parsed.netloc.lower()
            if not any(allowed in domain for allowed in allowed_domains):
                raise PathValidationError(
                    f"Domain {domain} not in allowed domains"
                )
        
        return True
        
    except Exception as e:
        logger.error(f"URL validation error: {str(e)}")
        raise PathValidationError(f"Invalid URL: {str(e)}")

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for security.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: The sanitized filename
    """
    # Remove path traversal attempts
    filename = filename.replace('..', '')
    
    # Remove directory separators
    filename = filename.replace('/', '').replace('\\', '')
    
    # Remove null bytes
    filename = filename.replace('\0', '')
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    return filename 