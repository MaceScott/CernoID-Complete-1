import shutil
import os
from pathlib import Path

def clean_project():
    """Final cleanup to remove duplicates and consolidate code"""
    root = Path.cwd()
    print("Starting final cleanup...")

    # 1. Remove duplicate/nested CernoID-Complete
    nested_dir = root / "CernoID-Complete"
    if nested_dir.exists():
        print("Removing nested project directory...")
        shutil.rmtree(nested_dir)

    # 2. Consolidate source code
    src_files = {
        'cerno_gui.py': 'src/core/',
        'individual_registration.py': 'src/face_recognition/',
        'notifications.py': 'src/services/',
        'main.py': 'src/',
        'script.py': 'src/utils/',
        'fix_imports.py': 'src/utils/'
    }

    print("\nConsolidating source code...")
    for file_name, dest_dir in src_files.items():
        # Find all instances of the file
        found_files = list(root.rglob(file_name))
        if found_files:
            # Move the first instance to the correct location
            dest_path = root / dest_dir
            dest_path.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(found_files[0], dest_path / file_name)
                print(f"Moved {file_name} to {dest_dir}")
            except Exception as e:
                print(f"Error moving {file_name}: {e}")

    # 3. Remove redundant directories
    redundant_dirs = [
        'dependencies',
        'backup',
        'config_backup',
        'backend',
        'app',
        'gui',
        '__pycache__'
    ]

    print("\nRemoving redundant directories...")
    for dir_name in redundant_dirs:
        for dir_path in root.rglob(dir_name):
            try:
                shutil.rmtree(dir_path)
                print(f"Removed {dir_path}")
            except Exception as e:
                print(f"Could not remove {dir_path}: {e}")

    # 4. Clean up virtual environments
    print("\nCleaning up Python environments...")
    env_dirs = ['venv', '.env', 'anaconda3']
    for env_dir in env_dirs:
        env_path = root / env_dir
        if env_path.exists():
            try:
                shutil.rmtree(env_path)
                print(f"Removed {env_dir}")
            except Exception as e:
                print(f"Could not remove {env_dir}: {e}")

    # 5. Ensure clean structure
    clean_structure = {
        'src': ['core', 'api', 'face_recognition', 'services', 'utils'],
        'frontend': ['src', 'public', 'components'],
        'deployment': ['docker', 'k8s'],
        'docs': ['api', 'setup', 'deployment'],
        'tests': ['unit', 'integration'],
        'scripts': ['deployment', 'maintenance']
    }

    print("\nEnsuring clean directory structure...")
    for main_dir, subdirs in clean_structure.items():
        main_path = root / main_dir
        main_path.mkdir(exist_ok=True)
        for subdir in subdirs:
            (main_path / subdir).mkdir(exist_ok=True)

    print("\nCleanup completed! Current structure:")
    for item in root.glob('*'):
        if item.is_dir() and not item.name.startswith('.'):
            print(f"\n- {item.name}/")
            for subitem in item.glob('*'):
                if subitem.is_dir():
                    print(f"  └── {subitem.name}/")

if __name__ == '__main__':
    clean_project() 