import shutil
import os
from pathlib import Path
import time

def safe_copy(source, dest):
    """Safely copy a file with retries"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            if not dest.parent.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
            if source.exists():
                shutil.copy2(source, dest)
                print(f"Successfully copied: {source.name} → {dest}")
                return True
        except PermissionError:
            if attempt < max_attempts - 1:
                print(f"File in use, waiting to retry: {source.name}")
                time.sleep(2)  # Wait 2 seconds before retry
            else:
                print(f"Could not copy {source.name} - file in use")
                return False
    return False

def restructure_project():
    """Create a clean, deployable project structure"""
    root = Path.cwd()
    print(f"Working in directory: {root}")
    
    # First, create the basic structure
    base_dirs = ['src', 'frontend', 'scripts', 'tests', 'docs', 'deployment']
    for dir_name in base_dirs:
        dir_path = root / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"Created directory: {dir_name}/")

    # Try to move Python files to src
    print("\nMoving Python files to src/...")
    for py_file in root.glob('*.py'):
        if py_file.name != 'final_restructure_v2.py':
            dest_path = root / 'src' / py_file.name
            safe_copy(py_file, dest_path)

    # Move configuration files to deployment
    print("\nMoving configuration files...")
    config_files = ['docker-compose.yml', 'Dockerfile', '.env.example']
    for config_file in config_files:
        source = root / config_file
        dest = root / 'deployment' / config_file
        if source.exists():
            safe_copy(source, dest)

    print("\nCurrent directory structure:")
    for item in root.glob('*'):
        if item.is_dir() and not item.name.startswith('.'):
            print(f"- {item.name}/")
            # List contents of each directory
            for subitem in item.glob('*'):
                print(f"  └── {subitem.name}")

    print("\nRestructure completed!")
    print("\nNext steps:")
    print("1. Close any applications that might be using project files")
    print("2. Run 'python scripts/cleanup.py' to remove redundant files")
    print("3. Check the 'src' directory for all moved Python files")

if __name__ == '__main__':
    restructure_project() 