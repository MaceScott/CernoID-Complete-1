#!/usr/bin/env python3
import os
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EnvVar:
    name: str
    required: bool
    description: str
    default: Optional[str] = None
    validate_func: Optional[callable] = None

def validate_url(value: str) -> bool:
    """Validate URL format."""
    return value.startswith(('http://', 'https://', 'ws://', 'wss://'))

def validate_port(value: str) -> bool:
    """Validate port number."""
    try:
        port = int(value)
        return 1 <= port <= 65535
    except ValueError:
        return False

def validate_bool(value: str) -> bool:
    """Validate boolean value."""
    return value.lower() in ('true', 'false', '1', '0')

def validate_float(value: str) -> bool:
    """Validate float value."""
    try:
        float(value)
        return True
    except ValueError:
        return False

def validate_int(value: str) -> bool:
    """Validate integer value."""
    try:
        int(value)
        return True
    except ValueError:
        return False

# Define required environment variables for frontend
FRONTEND_VARS = [
    EnvVar("NEXT_PUBLIC_APP_NAME", True, "Application name"),
    EnvVar("NEXT_PUBLIC_APP_DESCRIPTION", True, "Application description"),
    EnvVar("NEXT_PUBLIC_API_URL", True, "Backend API URL", validate_func=validate_url),
    EnvVar("NEXT_PUBLIC_APP_URL", True, "Frontend application URL", validate_func=validate_url),
    EnvVar("NEXT_PUBLIC_WS_URL", True, "WebSocket URL", validate_func=validate_url),
    EnvVar("NEXT_PUBLIC_ENABLE_FACE_RECOGNITION", True, "Enable face recognition", validate_func=validate_bool),
    EnvVar("NEXT_PUBLIC_ENABLE_NOTIFICATIONS", True, "Enable notifications", validate_func=validate_bool),
    EnvVar("NEXTAUTH_URL", True, "NextAuth.js URL", validate_func=validate_url),
    EnvVar("NEXTAUTH_SECRET", True, "NextAuth.js secret key"),
    EnvVar("PORT", False, "Frontend port", "3000", validate_func=validate_port),
]

# Define required environment variables for backend
BACKEND_VARS = [
    EnvVar("ENVIRONMENT", True, "Environment (development/production)"),
    EnvVar("DEBUG", True, "Debug mode", validate_func=validate_bool),
    EnvVar("BACKEND_HOST", True, "Backend host"),
    EnvVar("BACKEND_PORT", True, "Backend port", validate_func=validate_port),
    EnvVar("BACKEND_WORKERS", True, "Number of worker processes", validate_func=validate_int),
    EnvVar("DATABASE_URL", True, "Database connection URL"),
    EnvVar("DB_USER", True, "Database user"),
    EnvVar("DB_PASSWORD", True, "Database password"),
    EnvVar("DB_NAME", True, "Database name"),
    EnvVar("REDIS_URL", True, "Redis connection URL"),
    EnvVar("JWT_SECRET", True, "JWT secret key"),
    EnvVar("CORS_ORIGIN", True, "CORS origin URL", validate_func=validate_url),
    EnvVar("SECRET_KEY", True, "Application secret key"),
    EnvVar("FACE_DETECTION_CONFIDENCE", True, "Face detection confidence", validate_func=validate_float),
    EnvVar("FACE_ENCODING_TOLERANCE", True, "Face encoding tolerance", validate_func=validate_float),
    EnvVar("LOG_LEVEL", True, "Logging level"),
    EnvVar("SMTP_HOST", False, "SMTP server host"),
    EnvVar("SMTP_PORT", False, "SMTP server port", validate_func=validate_port),
    EnvVar("SMTP_USER", False, "SMTP username"),
    EnvVar("SMTP_PASSWORD", False, "SMTP password"),
    EnvVar("SMTP_FROM", False, "SMTP from address"),
]

def validate_env_vars(vars_list: List[EnvVar], env_file: str) -> List[str]:
    """Validate environment variables against a list of required variables."""
    errors = []
    env_path = Path(env_file)
    
    if not env_path.exists():
        errors.append(f"Environment file not found: {env_file}")
        return errors
    
    # Read environment file
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
                except ValueError:
                    continue
    
    # Validate each required variable
    for var in vars_list:
        value = env_vars.get(var.name)
        
        if var.required and not value:
            errors.append(f"Missing required variable: {var.name}")
            continue
        
        if value and var.validate_func and not var.validate_func(value):
            errors.append(f"Invalid value for {var.name}: {value}")
    
    return errors

def main():
    """Main function to validate environment variables."""
    errors = []
    
    # Validate frontend environment
    frontend_errors = validate_env_vars(FRONTEND_VARS, "frontend/.env")
    if frontend_errors:
        errors.extend(["Frontend Environment Errors:"] + frontend_errors)
    
    # Validate backend environment
    backend_errors = validate_env_vars(BACKEND_VARS, "backend/.env")
    if backend_errors:
        errors.extend(["Backend Environment Errors:"] + backend_errors)
    
    # Validate root environment
    root_errors = validate_env_vars(FRONTEND_VARS + BACKEND_VARS, ".env")
    if root_errors:
        errors.extend(["Root Environment Errors:"] + root_errors)
    
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    else:
        print("Environment validation successful!")

if __name__ == "__main__":
    main() 