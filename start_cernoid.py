"""CernoID Startup Script"""
import os
import sys
import subprocess
import platform
import time
from pathlib import Path
import webbrowser
import threading

def get_project_root():
    return Path(__file__).parent.absolute()

def is_docker_running():
    try:
        subprocess.run(['docker', 'info'], capture_output=True, check=True)
        return True
    except:
        return False

def start_docker_compose():
    subprocess.run(['docker-compose', 'up', '-d'], check=True)

def start_dev_mode():
    os.chdir('frontend')
    subprocess.Popen(['npm', 'install'])
    subprocess.Popen(['npm', 'run', 'dev'])
    
    os.chdir('../backend')
    subprocess.Popen(['pip', 'install', '-r', 'requirements.txt'])
    subprocess.Popen(['python', '-m', 'uvicorn', 'main:app', '--reload'])

def open_browser():
    """Open the frontend in the default browser after a short delay"""
    time.sleep(8)  # Wait longer for npm install and server start
    webbrowser.open('http://localhost:3000')

def setup_frontend():
    """Setup and run the Next.js frontend"""
    frontend_dir = Path(__file__).parent / 'frontend'
    os.chdir(str(frontend_dir))
    
    print("Installing frontend dependencies...")
    # Run npm install
    result = subprocess.run(
        ['npm', 'install'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Error installing frontend dependencies:")
        print(result.stderr)
        return False
        
    print("Starting frontend server...")
    # Start Next.js development server
    subprocess.Popen(
        ['npm', 'run', 'dev'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    return True

def run_backend():
    """Run the FastAPI backend server"""
    # Get the absolute path to the backend directory
    backend_dir = Path(__file__).parent / 'backend'
    src_dir = backend_dir / 'src'
    
    # Add both backend and backend/src to Python path
    sys.path.insert(0, str(backend_dir))
    sys.path.insert(0, str(src_dir))
    
    # Set environment variables
    os.environ['ENVIRONMENT'] = 'development'
    os.environ['DEBUG'] = 'false'
    os.environ['PYTHONPATH'] = f"{str(backend_dir)};{str(src_dir)}"
    
    print("Starting backend server...")
    
    # Change to the backend/src directory
    os.chdir(str(src_dir))
    
    # Import and run the application
    from main import app
    import uvicorn
    
    # Run the application with a single worker
    uvicorn.run(
        app,
        host="127.0.0.1",  # Only listen on localhost
        port=8000,
        log_level="info"
    )

def run_app():
    """Run the complete CernoID application."""
    print("Starting CernoID...")
    
    # Setup and start frontend in a separate thread
    frontend_thread = threading.Thread(target=setup_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    # Start browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Run backend in main thread
    run_backend()

def main():
    root_dir = get_project_root()
    os.chdir(root_dir)

    print("Starting CernoID...")
    
    # Check if --dev flag is passed
    dev_mode = '--dev' in sys.argv
    
    if dev_mode:
        print("Starting in development mode...")
        start_dev_mode()
    else:
        if not is_docker_running():
            print("Docker is not running. Please start Docker and try again.")
            sys.exit(1)
        
        print("Starting in production mode with Docker...")
        start_docker_compose()
        
        # Wait for services to be ready
        time.sleep(5)
        
        # Open browser
        url = "http://localhost:3000/login"
        if platform.system() == 'Windows':
            os.system(f'start {url}')
        elif platform.system() == 'Darwin':
            os.system(f'open {url}')
        else:
            os.system(f'xdg-open {url}')

if __name__ == "__main__":
    main() 