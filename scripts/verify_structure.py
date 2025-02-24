import os
from pathlib import Path
import sys

def verify_project_structure():
    """Verify the project structure matches expected layout"""
    root = Path.cwd()
    issues = []
    
    # Required directories
    required_dirs = {
        'src': ['core', 'api', 'face_recognition'],
        'frontend': ['src', 'public'],
        'scripts': [],
        'alembic': ['versions']
    }
    
    # Required files
    required_files = [
        'docker-compose.yml',
        'requirements.txt',
        '.env',
        'src/main.py',
        'scripts/deploy.py'
    ]
    
    # Check required directories
    for dir_name, subdirs in required_dirs.items():
        dir_path = root / dir_name
        if not dir_path.exists():
            issues.append(f"Missing directory: {dir_name}")
        else:
            for subdir in subdirs:
                subdir_path = dir_path / subdir
                if not subdir_path.exists():
                    issues.append(f"Missing subdirectory: {dir_name}/{subdir}")
    
    # Check required files
    for file_path in required_files:
        if not (root / file_path).exists():
            issues.append(f"Missing file: {file_path}")
    
    # Print results
    if issues:
        print("\n❌ Project structure verification failed!")
        print("\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before proceeding with deployment.")
        return False
    else:
        print("\n✅ Project structure verification passed!")
        print("\nCurrent structure:")
        print_directory_tree(root)
        return True

def print_directory_tree(path, prefix="", is_last=True):
    """Print a visual directory tree"""
    if path.name.startswith('.') or path.name == '__pycache__':
        return
        
    print(prefix + ("└── " if is_last else "├── ") + path.name)
    
    if path.is_dir():
        entries = [x for x in path.iterdir() 
                  if not x.name.startswith('.') and x.name != '__pycache__']
        entries = sorted(entries, key=lambda x: (not x.is_dir(), x.name))
        
        for i, entry in enumerate(entries):
            is_last_entry = i == len(entries) - 1
            print_directory_tree(
                entry,
                prefix + ("    " if is_last else "│   "),
                is_last_entry
            )

if __name__ == '__main__':
    success = verify_project_structure()
    sys.exit(0 if success else 1) 