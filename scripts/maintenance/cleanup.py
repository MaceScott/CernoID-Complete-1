#!/usr/bin/env python3

import os
import shutil
import sys
from pathlib import Path
from typing import List, Set

class ProjectCleaner:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.temp_dirs = {'.pytest_cache', '__pycache__', '.mypy_cache', '.coverage', 'node_modules'}
        self.temp_files = {'.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.pyd', '.Python', '*.so'}
        
    def clean_temp_files(self) -> None:
        """Remove temporary files and directories."""
        print("Cleaning temporary files and directories...")
        for path in Path(self.root_dir).rglob('*'):
            if path.is_dir() and path.name in self.temp_dirs:
                shutil.rmtree(path, ignore_errors=True)
                print(f"Removed directory: {path}")
            elif path.is_file():
                if path.name in self.temp_files or any(path.match(pattern) for pattern in self.temp_files):
                    path.unlink()
                    print(f"Removed file: {path}")

    def clean_empty_directories(self) -> None:
        """Remove empty directories."""
        print("\nRemoving empty directories...")
        for dirpath, dirnames, filenames in os.walk(self.root_dir, topdown=False):
            if not dirnames and not filenames and dirpath != str(self.root_dir):
                os.rmdir(dirpath)
                print(f"Removed empty directory: {dirpath}")

    def organize_imports(self) -> None:
        """Organize and clean up Python imports."""
        print("\nOrganizing Python imports...")
        try:
            import isort
            for py_file in Path(self.root_dir).rglob('*.py'):
                isort.file(py_file)
                print(f"Organized imports in: {py_file}")
        except ImportError:
            print("isort not installed. Skipping import organization.")

    def clean_requirements(self) -> None:
        """Clean and deduplicate requirements files."""
        print("\nCleaning requirements files...")
        req_files = list(Path(self.root_dir).rglob('requirements*.txt'))
        for req_file in req_files:
            if req_file.is_file():
                requirements = set()
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            requirements.add(line)
                
                with open(req_file, 'w') as f:
                    for req in sorted(requirements):
                        f.write(f"{req}\n")
                print(f"Cleaned requirements file: {req_file}")

    def run(self, clean_temp: bool = True, clean_empty: bool = True,
            organize_imports: bool = True, clean_reqs: bool = True) -> None:
        """Run the cleaning process with specified options."""
        if clean_temp:
            self.clean_temp_files()
        if clean_empty:
            self.clean_empty_directories()
        if organize_imports:
            self.organize_imports()
        if clean_reqs:
            self.clean_requirements()
        print("\nCleanup completed successfully!")

def main():
    if len(sys.argv) < 2:
        print("Usage: cleanup.py <project_root_directory>")
        sys.exit(1)

    root_dir = sys.argv[1]
    if not os.path.isdir(root_dir):
        print(f"Error: Directory '{root_dir}' does not exist.")
        sys.exit(1)

    cleaner = ProjectCleaner(root_dir)
    cleaner.run()

if __name__ == '__main__':
    main() 