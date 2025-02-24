import shutil
import os
from pathlib import Path

def cleanup_project_structure():
    """Reorganize project structure to match deployment requirements"""
    root = Path.cwd()
    
    # Create main directories if they don't exist
    main_dirs = ['src', 'frontend', 'scripts', 'alembic']
    for dir_name in main_dirs:
        (root / dir_name).mkdir(exist_ok=True)

    # Move backend files to src
    if (root / 'backend').exists():
        backend_path = root / 'backend'
        src_path = root / 'src'
        for item in backend_path.glob('*'):
            if item.is_file():
                shutil.move(str(item), str(src_path / item.name))
            elif item.is_dir() and item.name not in ['__pycache__']:
                shutil.move(str(item), str(src_path / item.name))

    # Consolidate face recognition related code
    face_dirs = ['face_recognition', 'faces']
    for dir_name in face_dirs:
        if (root / dir_name).exists():
            face_path = root / dir_name
            src_path = root / 'src' / 'face_recognition'
            src_path.mkdir(exist_ok=True)
            for item in face_path.glob('*'):
                if item.name != '__pycache__':
                    target = src_path / item.name
                    if not target.exists():
                        shutil.move(str(item), str(target))

    # Move GUI related files
    if (root / 'gui').exists():
        gui_path = root / 'gui'
        frontend_path = root / 'frontend'
        for item in gui_path.glob('*'):
            if item.name != '__pycache__':
                target = frontend_path / item.name
                if not target.exists():
                    shutil.move(str(item), str(target))

    # Create backup of configuration files
    config_files = ['.env', '.env.example', 'docker-compose.yml', 'requirements.txt']
    backup_dir = root / 'backup_config'
    backup_dir.mkdir(exist_ok=True)
    for file in config_files:
        if (root / file).exists():
            shutil.copy2(str(root / file), str(backup_dir / file))

    print("Project structure cleanup completed!")

if __name__ == '__main__':
    cleanup_project_structure() 