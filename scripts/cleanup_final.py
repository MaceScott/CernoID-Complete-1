import shutil
import os
from pathlib import Path

def cleanup_final():
    """Final consolidation of project directories"""
    root = Path.cwd()
    
    # Directories to merge into src/
    src_dirs = {
        'app': 'src/app',
        'backend': 'src/backend',
        'core': 'src/core',
        'face_recognition': 'src/face_recognition',
        'faces': 'src/face_recognition/faces'
    }
    
    # Directories to merge into frontend/
    frontend_dirs = {
        'gui': 'frontend/components',
        'assets': 'frontend/public/assets'
    }
    
    # Directories to keep as-is
    keep_dirs = {
        '.git',
        '.github',
        'alembic',
        'docs',
        'k8s',
        'scripts',
        'src',
        'frontend',
        'tests',
        'venv'
    }
    
    print("Starting final cleanup...")
    
    # Merge directories into src
    for source, dest in src_dirs.items():
        source_path = root / source
        dest_path = root / dest
        if source_path.exists():
            print(f"Moving {source} → {dest}")
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                if dest_path.exists():
                    # Merge contents if destination exists
                    for item in source_path.glob('*'):
                        if item.is_file():
                            shutil.copy2(item, dest_path)
                        elif item.is_dir() and item.name != '__pycache__':
                            shutil.copytree(item, dest_path / item.name, 
                                         dirs_exist_ok=True)
                else:
                    # Move entire directory if destination doesn't exist
                    shutil.copytree(source_path, dest_path)
                shutil.rmtree(source_path)
            except Exception as e:
                print(f"Error processing {source}: {e}")

    # Merge directories into frontend
    for source, dest in frontend_dirs.items():
        source_path = root / source
        dest_path = root / dest
        if source_path.exists():
            print(f"Moving {source} → {dest}")
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                if dest_path.exists():
                    for item in source_path.glob('*'):
                        if item.is_file():
                            shutil.copy2(item, dest_path)
                        elif item.is_dir() and item.name != '__pycache__':
                            shutil.copytree(item, dest_path / item.name, 
                                         dirs_exist_ok=True)
                else:
                    shutil.copytree(source_path, dest_path)
                shutil.rmtree(source_path)
            except Exception as e:
                print(f"Error processing {source}: {e}")

    # Remove unnecessary directories
    for item in root.glob('*'):
        if (item.is_dir() and 
            item.name not in keep_dirs and 
            not item.name.startswith('.')):
            try:
                print(f"Removing {item.name}/")
                shutil.rmtree(item)
            except Exception as e:
                print(f"Error removing {item.name}: {e}")

    print("\nCleanup completed! Final structure:")
    for item in root.glob('*'):
        if item.is_dir() and not item.name.startswith('__'):
            print(f"- {item.name}/")

if __name__ == '__main__':
    cleanup_final() 