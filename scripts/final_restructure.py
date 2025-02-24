import shutil
import os
from pathlib import Path

def restructure_project():
    """Create a clean, deployable project structure"""
    root = Path.cwd()
    
    # Define the clean structure we want
    clean_structure = {
        'src': {
            'api': ['routes', 'models', 'schemas'],
            'core': ['config', 'security', 'utils'],
            'face_recognition': ['models', 'utils'],
            'services': ['recognition', 'notification', 'monitoring'],
            'database': ['models', 'migrations'],
        },
        'frontend': {
            'src': ['components', 'hooks', 'utils', 'styles'],
            'public': ['assets'],
        },
        'scripts': ['deployment', 'maintenance'],
        'tests': ['unit', 'integration'],
        'docs': ['api', 'setup', 'deployment'],
        'deployment': ['docker', 'k8s']
    }

    # Essential files that should be in root
    essential_files = [
        'main.py',
        'requirements.txt',
        'docker-compose.yml',
        'Dockerfile',
        '.env.example',
        'README.md'
    ]

    print("Starting project restructure...")

    # Create clean structure
    for main_dir, subdirs in clean_structure.items():
        main_path = root / main_dir
        main_path.mkdir(exist_ok=True)
        if isinstance(subdirs, list):
            for subdir in subdirs:
                (main_path / subdir).mkdir(parents=True, exist_ok=True)
        else:
            for subdir, subsubdirs in subdirs.items():
                subdir_path = main_path / subdir
                subdir_path.mkdir(parents=True, exist_ok=True)
                for subsubdir in subsubdirs:
                    (subdir_path / subsubdir).mkdir(parents=True, exist_ok=True)

    # Move important files to their new locations
    moves = {
        'src/main.py': 'src/main.py',
        'src/cerno_gui.py': 'src/core/gui.py',
        'src/individual_registration.py': 'src/services/recognition/registration.py',
        'src/notifications.py': 'src/services/notification/service.py',
    }

    for source, dest in moves.items():
        source_path = root / source
        dest_path = root / dest
        if source_path.exists():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            print(f"Moved {source} → {dest}")

    # Consolidate and move core functionality
    consolidations = {
        'src/face_recognition': 'src/face_recognition',
        'src/api': 'src/api',
        'src/core': 'src/core',
        'src/services': 'src/services',
        'frontend/components': 'frontend/src/components'
    }

    for source, dest in consolidations.items():
        source_path = root / source
        dest_path = root / dest
        if source_path.exists():
            if dest_path.exists():
                # Merge directories
                for item in source_path.glob('*'):
                    if item.is_file():
                        shutil.copy2(item, dest_path)
                    elif item.is_dir() and item.name != '__pycache__':
                        shutil.copytree(item, dest_path / item.name, 
                                      dirs_exist_ok=True)
            else:
                # Move directory
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)

    # Remove redundant directories
    redundant_dirs = [
        'src/backup',
        'src/config_backup',
        'src/gui',
        'src/tools',
        'src/frontend',
        'src/backend',
        'src/cernoid'
    ]

    for dir_path in redundant_dirs:
        full_path = root / dir_path
        if full_path.exists():
            shutil.rmtree(full_path)
            print(f"Removed redundant directory: {dir_path}")

    print("\nProject restructure completed!")
    print("\nFinal structure (main directories):")
    for item in root.glob('*'):
        if item.is_dir() and not item.name.startswith('.'):
            print(f"- {item.name}/")

if __name__ == '__main__':
    restructure_project() 