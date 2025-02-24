import shutil
import os
from pathlib import Path
import datetime

def cleanup_project_structure():
    """Reorganize project structure without touching dependencies"""
    root = Path.cwd()
    
    # Create main directories
    main_dirs = ['src', 'frontend', 'scripts', 'alembic']
    for dir_name in main_dirs:
        (root / dir_name).mkdir(exist_ok=True)
        print(f"Created directory: {dir_name}")

    # Skip these problematic directories
    skip_dirs = ['dependencies', 'anaconda3', '__pycache__']
    
    # Move Python files to src
    for file in root.glob('*.py'):
        if file.name != 'cleanup_v3.py':
            try:
                shutil.move(str(file), str(root / 'src' / file.name))
                print(f"Moved {file.name} to src/")
            except Exception as e:
                print(f"Could not move {file.name}: {e}")

    print("\nCleanup completed!")
    print("\nCurrent directory structure:")
    for item in root.glob('*'):
        if item.is_dir() and item.name not in skip_dirs:
            print(f"- {item.name}/")

if __name__ == '__main__':
    cleanup_project_structure() 