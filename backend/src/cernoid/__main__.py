"""CernoID Face Recognition System - Main Entry Point"""

import os
import sys
import logging
import webbrowser
from pathlib import Path
import subprocess
import time
import signal
import threading
from typing import Optional, Tuple
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_startup_message():
    """Print a helpful startup message."""
    clear_screen()
    message = """
╔════════════════════════════════════════════════════════════════╗
║                   CernoID System Startup                       ║
╚════════════════════════════════════════════════════════════════╝

Starting CernoID system components...

1. Backend API Server (FastAPI)
   - URL: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Swagger UI: http://localhost:8000/swagger

2. Frontend UI Server (Next.js)
   - URL: http://localhost:3000

3. Database (PostgreSQL)
   - Port: 5432

4. Cache (Redis)
   - Port: 6379

Press Ctrl+C to stop all servers
"""
    print(message)

def check_docker() -> Tuple[bool, str]:
    """Check if Docker is available and running."""
    if not shutil.which('docker'):
        return False, "Docker not found. Please install Docker Desktop."
    
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        return False, "Docker daemon not running. Please start Docker Desktop."
    except Exception:
        return False, "Docker not accessible. Please ensure Docker Desktop is installed and running."

def check_docker_compose() -> Tuple[bool, str]:
    """Check if docker-compose is available."""
    if not shutil.which('docker-compose'):
        return False, "docker-compose not found. Please install Docker Desktop."
    
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        return False, "docker-compose not working correctly."
    except Exception:
        return False, "docker-compose not accessible. Please ensure Docker Desktop is installed."

def get_project_root() -> Path:
    """Get the absolute path to the project root directory."""
    current_file = Path(__file__).resolve()
    # Navigate up from backend/src/cernoid/__main__.py to project root
    return current_file.parent.parent.parent.parent

def ensure_env_file():
    """Ensure .env file exists."""
    project_root = get_project_root()
    env_file = project_root / '.env'
    env_example = project_root / '.env.example'
    
    if not env_file.exists() and env_example.exists():
        print("\nCreating .env file from .env.example...")
        env_example.rename(env_file)

def start_services():
    """Start all services using docker-compose."""
    try:
        project_root = get_project_root()
        
        # Check Docker availability
        docker_ok, docker_msg = check_docker()
        if not docker_ok:
            print(f"\nError: {docker_msg}")
            sys.exit(1)
        
        # Check docker-compose availability
        compose_ok, compose_msg = check_docker_compose()
        if not compose_ok:
            print(f"\nError: {compose_msg}")
            sys.exit(1)
        
        # Ensure .env file exists
        ensure_env_file()
        
        print("\nStarting CernoID services...")
        
        # Start services with docker-compose
        process = subprocess.Popen(
            ['docker-compose', 'up', '--build'],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Monitor the output
        while True:
            output = process.stdout.readline() if process.stdout else ''
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # Check for errors
        if process.returncode != 0:
            stderr = process.stderr.read() if process.stderr else ''
            print(f"\nError starting services: {stderr}")
            sys.exit(1)
        
        # Open browser after services are up
        print("\nOpening application in browser...")
        webbrowser.open('http://localhost:3000')
        
        # Wait for Ctrl+C
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down services...")
        subprocess.run(
            ['docker-compose', 'down'],
            cwd=project_root,
            check=True
        )
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

def main():
    """Main entry point for the CernoID application."""
    try:
        print_startup_message()
        start_services()
    except KeyboardInterrupt:
        print("\nShutting down CernoID...")
    except Exception as e:
        print(f"\nApplication error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 