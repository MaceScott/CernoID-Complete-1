import shutil
import os
from pathlib import Path

def clean_src_directory():
    """Clean up the src directory structure"""
    root = Path.cwd()
    src_dir = root / 'dist' / 'cernoid' / 'src'
    
    # Define what we want to keep
    keep_files = {
        'main.py',
        'cerno_gui.py',
        'individual_registration.py',
        'notifications.py',
        '__init__.py'
    }
    
    # Define the clean structure we want
    clean_structure = {
        'core': ['config', 'utils'],
        'api': ['routes', 'controllers'],
        'face_recognition': ['models', 'utils'],
        'services': ['recognition', 'monitoring'],
        'database': ['models', 'migrations']
    }
    
    print("Cleaning src directory...")
    
    # Create temp directory for files we want to keep
    temp_dir = root / 'temp_files'
    temp_dir.mkdir(exist_ok=True)
    
    # Save important files
    for file in keep_files:
        if (src_dir / file).exists():
            shutil.copy2(src_dir / file, temp_dir / file)
            print(f"Saved: {file}")
    
    # Remove everything in src
    for item in src_dir.glob('*'):
        try:
            if item.is_file():
                os.remove(item)
            else:
                shutil.rmtree(item)
            print(f"Removed: {item.name}")
        except Exception as e:
            print(f"Could not remove {item.name}: {e}")
    
    # Create clean structure
    for dir_name, subdirs in clean_structure.items():
        dir_path = src_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        for subdir in subdirs:
            (dir_path / subdir).mkdir(exist_ok=True)
        print(f"Created: {dir_name}/")
    
    # Restore important files
    for file in keep_files:
        if (temp_dir / file).exists():
            shutil.copy2(temp_dir / file, src_dir / file)
            print(f"Restored: {file}")
    
    # Clean up temp directory
    shutil.rmtree(temp_dir)
    
    print("\nSrc directory cleaned! Structure:")
    for item in src_dir.glob('*'):
        print(f"\n- {item.name}/")
        if item.is_dir():
            for subitem in item.glob('*'):
                print(f"  └── {subitem.name}/")

if __name__ == '__main__':
    clean_src_directory() 