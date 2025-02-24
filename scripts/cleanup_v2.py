import shutil
import os
from pathlib import Path
import datetime

def backup_directory(source_dir: Path, backup_name: str = None):
    """Create a backup of the directory"""
    if backup_name is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
    
    backup_dir = source_dir.parent / backup_name
    backup_dir.mkdir(exist_ok=True)
    return backup_dir

def cleanup_project_structure():
    """Reorganize project structure to match deployment requirements"""
    root = Path.cwd()
    
    # Create backup
    backup_dir = backup_directory(root)
    print(f"Creating backup in: {backup_dir}")

    # Core directories to keep
    core_dirs = {
        'src': ['core', 'api', 'face_recognition'],
        'frontend': ['components', 'public', 'src'],
        'scripts': [],
        'alembic': ['versions']
    }

    # Create main directories
    for dir_name in core_dirs:
        (root / dir_name).mkdir(exist_ok=True)

    # Move and consolidate directories
    moves = {
        'backend': 'src',
        'core': 'src/core',
        'face_recognition': 'src/face_recognition',
        'faces': 'src/face_recognition/faces',
        'gui': 'frontend',
        'app': 'src/app',
        'config': 'src/config'
    }

    # Backup and move directories
    for source, dest in moves.items():
        source_path = root / source
        dest_path = root / dest
        if source_path.exists():
            print(f"Moving {source} to {dest}")
            dest_path.mkdir(parents=True, exist_ok=True)
            # Backup first
            shutil.copytree(source_path, backup_dir / source, dirs_exist_ok=True)
            # Move contents
            for item in source_path.glob('*'):
                if item.name != '__pycache__':
                    try:
                        target = dest_path / item.name
                        if not target.exists():
                            if item.is_file():
                                shutil.copy2(item, target)
                            else:
                                shutil.copytree(item, target, dirs_exist_ok=True)
                    except Exception as e:
                        print(f"Error moving {item}: {e}")

    # Essential files to keep in root
    essential_files = [
        '.env',
        '.env.example',
        'docker-compose.yml',
        'requirements.txt',
        'Dockerfile',
        'README.md'
    ]

    # Backup and organize files
    for file in root.glob('*.py'):
        if file.name not in ['setup.py', 'manage.py']:
            # Backup first
            shutil.copy2(file, backup_dir / file.name)
            # Move to appropriate location
            if file.name == 'main.py':
                shutil.copy2(file, root / 'src' / file.name)
            else:
                shutil.copy2(file, root / 'scripts' / file.name)

    # Clean up directories that should be removed
    dirs_to_remove = [
        '.pytest_cache',
        'test_images',
        'external_models',
        'dependencies',
        'credentials',
        'images',
        'logs'
    ]

    for dir_name in dirs_to_remove:
        dir_path = root / dir_name
        if dir_path.exists():
            print(f"Backing up and removing {dir_name}")
            shutil.copytree(dir_path, backup_dir / dir_name, dirs_exist_ok=True)
            shutil.rmtree(dir_path)

    print("\nCleanup completed!")
    print(f"Backup created in: {backup_dir}")
    print("\nPlease verify the new structure and check the backup directory if you need to recover any files.")

if __name__ == '__main__':
    cleanup_project_structure() 