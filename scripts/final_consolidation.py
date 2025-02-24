import shutil
import os
from pathlib import Path

def consolidate_directories():
    """Consolidate and clean up the project structure"""
    root = Path.cwd()
    print("Starting final consolidation...")

    # 1. Define our target structure
    target_structure = {
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
        'docs': {
            'api': [],
            'setup': [],
            'deployment': []
        },
        'tests': {
            'unit': [],
            'integration': []
        }
    }

    # 2. Create clean structure
    for main_dir, subdirs in target_structure.items():
        main_path = root / main_dir
        if isinstance(subdirs, dict):
            for subdir, subsubdirs in subdirs.items():
                subdir_path = main_path / subdir
                subdir_path.mkdir(parents=True, exist_ok=True)
                for subsubdir in subsubdirs:
                    (subdir_path / subsubdir).mkdir(parents=True, exist_ok=True)

    # 3. Consolidate content from duplicate directories
    nested_project = root / "CernoID-Complete"
    if nested_project.exists():
        # Move content from nested directory to root
        for item in nested_project.glob('*'):
            if item.is_file():
                try:
                    shutil.copy2(item, root / item.name)
                except Exception as e:
                    print(f"Could not copy {item.name}: {e}")

    # 4. Move files to their correct locations
    file_mappings = {
        'docker-compose.yml': 'deployment/docker/',
        'Dockerfile': 'deployment/docker/',
        '.env.example': 'deployment/',
        'requirements.txt': '.',
        'README.md': '.',
        'face_encodings.pkl': 'src/face_recognition/models/'
    }

    for file_name, dest_dir in file_mappings.items():
        source = root / file_name
        dest = root / dest_dir / file_name
        if source.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(source, dest)
                print(f"Moved {file_name} to {dest_dir}")
            except Exception as e:
                print(f"Could not move {file_name}: {e}")

    # 5. Remove redundant directories
    dirs_to_remove = [
        'dependencies',
        'venv',
        'backup',
        'config_backup',
        'tools',
        '.idea',
        'CernoID-Complete'
    ]

    for dir_name in dirs_to_remove:
        dir_path = root / dir_name
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path, ignore_errors=True)
                print(f"Removed {dir_name}")
            except Exception as e:
                print(f"Could not remove {dir_name}: {e}")

    print("\nConsolidation completed! Current structure:")
    for item in root.glob('*'):
        if item.is_dir() and not item.name.startswith('.'):
            print(f"\n- {item.name}/")
            for subitem in item.glob('*'):
                if subitem.is_dir():
                    print(f"  └── {subitem.name}/")

    print("\nNext steps:")
    print("1. Review the consolidated structure")
    print("2. Test the application functionality")
    print("3. Update any import statements if needed")
    print("4. Remove any remaining unnecessary files manually")

if __name__ == '__main__':
    consolidate_directories() 