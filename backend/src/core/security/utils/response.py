from typing import Any, Dict, List, Optional, Union
import json
import logging
from fastapi.responses import JSONResponse
from ..logging.config import LogConfig

logger = LogConfig().get_logger(__name__)

def sanitize_response(
    data: Any,
    exclude_fields: Optional[List[str]] = None,
    mask_fields: Optional[List[str]] = None
) -> Any:
    """
    Sanitize response data by removing sensitive information.
    
    Args:
        data: Response data to sanitize
        exclude_fields: Fields to exclude from response
        mask_fields: Fields to mask in response
        
    Returns:
        Sanitized response data
    """
    try:
        if isinstance(data, dict):
            return _sanitize_dict(data, exclude_fields, mask_fields)
        elif isinstance(data, list):
            return [_sanitize_dict(item, exclude_fields, mask_fields) for item in data]
        else:
            return data
            
    except Exception as e:
        logger.error(f"Response sanitization error: {str(e)}")
        return data

def _sanitize_dict(
    data: Dict[str, Any],
    exclude_fields: Optional[List[str]] = None,
    mask_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Sanitize dictionary data.
    
    Args:
        data: Dictionary to sanitize
        exclude_fields: Fields to exclude
        mask_fields: Fields to mask
        
    Returns:
        Sanitized dictionary
    """
    result = {}
    
    for key, value in data.items():
        # Skip excluded fields
        if exclude_fields and key in exclude_fields:
            continue
            
        # Mask sensitive fields
        if mask_fields and key in mask_fields:
            result[key] = "********"
        # Recursively sanitize nested dictionaries
        elif isinstance(value, dict):
            result[key] = _sanitize_dict(value, exclude_fields, mask_fields)
        # Recursively sanitize nested lists
        elif isinstance(value, list):
            result[key] = [
                _sanitize_dict(item, exclude_fields, mask_fields)
                if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            result[key] = value
            
    return result

def create_sanitized_response(
    data: Any,
    status_code: int = 200,
    exclude_fields: Optional[List[str]] = None,
    mask_fields: Optional[List[str]] = None
) -> JSONResponse:
    """
    Create a sanitized JSON response.
    
    Args:
        data: Response data
        status_code: HTTP status code
        exclude_fields: Fields to exclude
        mask_fields: Fields to mask
        
    Returns:
        JSONResponse: Sanitized response
    """
    try:
        sanitized_data = sanitize_response(data, exclude_fields, mask_fields)
        return JSONResponse(
            content=sanitized_data,
            status_code=status_code
        )
    except Exception as e:
        logger.error(f"Response creation error: {str(e)}")
        return JSONResponse(
            content={"error": "Internal server error"},
            status_code=500
        )

def sanitize_error_response(
    error: Exception,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Create a sanitized error response.
    
    Args:
        error: Exception to handle
        include_traceback: Whether to include traceback
        
    Returns:
        Dict containing error details
    """
    try:
        error_response = {
            "error": str(error),
            "type": error.__class__.__name__
        }
        
        if include_traceback:
            import traceback
            error_response["traceback"] = traceback.format_exc()
            
        return error_response
        
    except Exception as e:
        logger.error(f"Error response creation error: {str(e)}")
        return {
            "error": "Internal server error",
            "type": "InternalError"
        } 