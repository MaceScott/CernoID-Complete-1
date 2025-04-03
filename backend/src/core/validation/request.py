from typing import Any, Dict, List, Optional, Union
from fastapi import Request, HTTPException
from pydantic import BaseModel, ValidationError
import logging
from ..security.utils.path_validation import validate_url
from ..logging.config import LogConfig

logger = LogConfig().get_logger(__name__)

class ValidationErrorResponse(BaseModel):
    """Response model for validation errors"""
    detail: List[Dict[str, Any]]

async def validate_request_params(
    request: Request,
    required_params: List[str],
    optional_params: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate request parameters.
    
    Args:
        request: FastAPI request object
        required_params: List of required parameters
        optional_params: List of optional parameters
        
    Returns:
        Dict containing validated parameters
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        params = {}
        
        # Get query parameters
        query_params = dict(request.query_params)
        
        # Validate required parameters
        for param in required_params:
            if param not in query_params:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required parameter: {param}"
                )
            params[param] = query_params[param]
        
        # Add optional parameters if present
        if optional_params:
            for param in optional_params:
                if param in query_params:
                    params[param] = query_params[param]
        
        return params
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Request parameter validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request parameters"
        )

async def validate_request_body(
    request: Request,
    model: type[BaseModel]
) -> BaseModel:
    """
    Validate request body against a Pydantic model.
    
    Args:
        request: FastAPI request object
        model: Pydantic model class
        
    Returns:
        Validated model instance
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        body = await request.json()
        return model(**body)
        
    except ValidationError as e:
        logger.error(f"Request body validation error: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=ValidationErrorResponse(detail=e.errors()).dict()
        )
    except Exception as e:
        logger.error(f"Request body parsing error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request body"
        )

async def validate_file_upload(
    request: Request,
    max_size: int = 10 * 1024 * 1024,  # 10MB
    allowed_types: Optional[List[str]] = None
) -> bytes:
    """
    Validate file upload.
    
    Args:
        request: FastAPI request object
        max_size: Maximum file size in bytes
        allowed_types: List of allowed MIME types
        
    Returns:
        bytes: File contents
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        content_type = request.headers.get("content-type", "")
        
        # Check content type
        if not content_type.startswith("multipart/form-data"):
            raise HTTPException(
                status_code=400,
                detail="Invalid content type"
            )
        
        # Get file
        form = await request.form()
        file = form.get("file")
        
        if not file:
            raise HTTPException(
                status_code=400,
                detail="No file uploaded"
            )
        
        # Check file size
        if len(file.file.read()) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size / (1024 * 1024)}MB"
            )
        
        # Check file type
        if allowed_types:
            file.file.seek(0)
            mime_type = file.content_type
            if mime_type not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
                )
        
        # Read file contents
        file.file.seek(0)
        return file.file.read()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid file upload"
        )

def validate_url_param(
    url: str,
    allowed_domains: Optional[List[str]] = None
) -> str:
    """
    Validate URL parameter.
    
    Args:
        url: URL to validate
        allowed_domains: List of allowed domains
        
    Returns:
        str: Validated URL
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        validate_url(url, allowed_domains)
        return url
    except Exception as e:
        logger.error(f"URL validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid URL"
        ) 