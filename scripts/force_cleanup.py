import shutil
import os
from pathlib import Path
import time

def force_cleanup():
    """Force cleanup of the project structure"""
    root = Path.cwd()
    print("Starting force cleanup...")

    # 1. Define the ONLY directories we want to keep
    essential_structure = {
        'src': {
            'core': ['config', 'utils'],
            'api': ['routes', 'controllers'],
            'face_recognition': ['models', 'utils'],
            'services': ['recognition', 'monitoring'],
            'database': ['models', 'migrations']
        },
        'frontend': {
            'src': ['components', 'hooks', 'utils'],
            'public': ['assets']
        },
        'deployment': {
            'docker': [],
            'k8s': []
        },
        'docs': ['api', 'setup', 'deployment'],
        'tests': ['unit', 'integration'],
        'scripts': ['deployment', 'maintenance']
    }

    # 2. Create temporary directory for essential files
    temp_dir = root / 'temp_migration'
    temp_dir.mkdir(exist_ok=True)

    try:
        # 3. Save essential files to temp directory
        essential_files = [
            'requirements.txt',
            'README.md',
            'face_encodings.pkl',
            '.env',
            '.env.example',
            'docker-compose.yml',
            'Dockerfile'
        ]

        print("Saving essential files...")
        for file_name in essential_files:
            file_path = root / file_name
            if file_path.exists():
                try:
                    shutil.copy2(file_path, temp_dir / file_name)
                    print(f"Saved: {file_name}")
                except Exception as e:
                    print(f"Could not save {file_name}: {e}")

        # 4. Remove everything except .git and temp directory
        print("\nRemoving old structure...")
        for item in root.glob('*'):
            if item.name not in ['.git', 'temp_migration']:
                try:
                    if item.is_file():
                        os.remove(item)
                    else:
                        shutil.rmtree(item)
                    print(f"Removed: {item.name}")
                except Exception as e:
                    print(f"Could not remove {item.name}: {e}")

        # 5. Create clean structure
        print("\nCreating clean structure...")
        for main_dir, subdirs in essential_structure.items():
            main_path = root / main_dir
            main_path.mkdir(exist_ok=True)
            if isinstance(subdirs, dict):
                for subdir, subsubdirs in subdirs.items():
                    subdir_path = main_path / subdir
                    subdir_path.mkdir(exist_ok=True)
                    for subsubdir in subsubdirs:
                        (subdir_path / subsubdir).mkdir(exist_ok=True)
            else:
                for subdir in subdirs:
                    (main_path / subdir).mkdir(exist_ok=True)

        # 6. Restore essential files
        print("\nRestoring essential files...")
        for file_name in essential_files:
            source = temp_dir / file_name
            if source.exists():
                if file_name in ['docker-compose.yml', 'Dockerfile']:
                    dest = root / 'deployment' / 'docker' / file_name
                elif file_name == 'face_encodings.pkl':
                    dest = root / 'src' / 'face_recognition' / 'models' / file_name
                else:
                    dest = root / file_name
                try:
                    shutil.copy2(source, dest)
                    print(f"Restored: {file_name}")
                except Exception as e:
                    print(f"Could not restore {file_name}: {e}")

    finally:
        # 7. Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    print("\nCleanup completed! Final structure:")
    for item in root.glob('*'):
        if item.is_dir() and not item.name.startswith('.'):
            print(f"\n- {item.name}/")
            for subitem in item.glob('*'):
                if subitem.is_dir():
                    print(f"  └── {subitem.name}/")

    print("\nNext steps:")
    print("1. Review the final structure")
    print("2. Move your source code files to appropriate directories")
    print("3. Update import statements if needed")
    print("4. Test the application")

if __name__ == '__main__':
    force_cleanup() 