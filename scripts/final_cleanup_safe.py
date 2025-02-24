import shutil
import os
from pathlib import Path
import stat

def handle_remove_readonly(func, path, exc):
    """Handle read-only files during deletion"""
    excvalue = exc[1]
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise

def safe_remove(path):
    """Safely remove a directory or file"""
    try:
        if path.is_file():
            os.chmod(path, stat.S_IRWXU)
            path.unlink()
        else:
            shutil.rmtree(path, ignore_errors=False, onerror=handle_remove_readonly)
        print(f"Successfully removed: {path}")
    except Exception as e:
        print(f"Could not remove {path}: {e}")

def clean_project():
    """Final cleanup with safe removal of files"""
    root = Path.cwd()
    print("Starting final cleanup...")

    # 1. First, let's identify what we have
    print("\nCurrent directory structure:")
    for item in root.glob('*'):
        print(f"Found: {item}")

    # 2. Create our target structure first
    clean_structure = {
        'src': ['core', 'api', 'face_recognition', 'services', 'utils'],
        'frontend': ['src', 'public', 'components'],
        'deployment': ['docker', 'k8s'],
        'docs': ['api', 'setup', 'deployment'],
        'tests': ['unit', 'integration'],
        'scripts': ['deployment', 'maintenance']
    }

    print("\nCreating clean directory structure...")
    for main_dir, subdirs in clean_structure.items():
        main_path = root / main_dir
        main_path.mkdir(exist_ok=True)
        for subdir in subdirs:
            (main_path / subdir).mkdir(exist_ok=True)
            print(f"Created: {main_dir}/{subdir}")

    # 3. Move important Python files to src
    print("\nMoving Python files...")
    for py_file in root.glob('*.py'):
        if py_file.name not in ['final_cleanup_safe.py']:
            try:
                dest = root / 'src' / py_file.name
                shutil.copy2(py_file, dest)
                print(f"Moved: {py_file.name} to src/")
            except Exception as e:
                print(f"Could not move {py_file.name}: {e}")

    # 4. Move configuration files to deployment
    print("\nMoving configuration files...")
    config_files = ['docker-compose.yml', 'Dockerfile', '.env.example']
    for config_file in config_files:
        source = root / config_file
        if source.exists():
            try:
                dest = root / 'deployment' / config_file
                shutil.copy2(source, dest)
                print(f"Moved: {config_file} to deployment/")
            except Exception as e:
                print(f"Could not move {config_file}: {e}")

    print("\nCleanup completed! Current structure:")
    for item in root.glob('*'):
        if item.is_dir() and not item.name.startswith('.'):
            print(f"\n- {item.name}/")
            for subitem in item.glob('*'):
                if subitem.is_dir():
                    print(f"  └── {subitem.name}/")

    print("\nNOTE: Some system files and directories were skipped for safety.")
    print("You may need to manually remove the nested CernoID-Complete directory.")

if __name__ == '__main__':
    clean_project() 