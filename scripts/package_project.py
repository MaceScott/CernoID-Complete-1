import shutil
import os
from pathlib import Path
import json

def package_project():
    """Package the project for deployment"""
    root = Path.cwd()
    print("Packaging project for deployment...")

    # Define core project files and directories
    core_structure = {
        'src': {
            'face_recognition': ['models', 'utils'],
            'core': ['config', 'utils'],
            'api': ['routes'],
            'services': ['recognition']
        },
        'frontend': {
            'src': ['components'],
            'public': ['assets']
        }
    }

    # Essential files that must be included
    essential_files = [
        'requirements.txt',
        'docker-compose.yml',
        'Dockerfile',
        '.env.example',
        'face_encodings.pkl'
    ]

    # Create dist directory for packaged project
    dist_dir = root / 'dist' / 'cernoid'
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True)

    # Copy core structure
    print("\nCopying core files...")
    for main_dir, subdirs in core_structure.items():
        src_dir = root / main_dir
        if src_dir.exists():
            dest_dir = dist_dir / main_dir
            shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
            print(f"Copied {main_dir}/")

    # Copy essential files
    print("\nCopying essential files...")
    for file_name in essential_files:
        src_file = root / file_name
        if src_file.exists():
            shutil.copy2(src_file, dist_dir)
            print(f"Copied {file_name}")

    # Create deployment instructions
    instructions = {
        "setup": [
            "1. Install Docker and Docker Compose",
            "2. Copy .env.example to .env and update settings",
            "3. Run 'docker-compose up -d' to start services",
            "4. Access the application at http://localhost:8000"
        ],
        "requirements": {
            "docker": "20.10+",
            "docker-compose": "1.29+",
            "ports_needed": [8000, 5432],
            "minimum_specs": {
                "ram": "4GB",
                "cpu": "2 cores",
                "storage": "10GB"
            }
        },
        "environment_variables": [
            "DB_HOST",
            "DB_USER",
            "DB_PASSWORD",
            "DB_NAME",
            "JWT_SECRET"
        ]
    }

    # Write deployment instructions
    with open(dist_dir / 'DEPLOY.json', 'w') as f:
        json.dump(instructions, f, indent=2)

    # Create quick start script
    quickstart = """#!/bin/bash
# Quick start script for CernoID

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from example..."
    cp .env.example .env
    echo "Please edit .env with your settings"
    exit 1
fi

# Start services
docker-compose up -d

echo "CernoID is starting..."
echo "Access the application at http://localhost:8000"
"""

    with open(dist_dir / 'quickstart.sh', 'w') as f:
        f.write(quickstart)
    os.chmod(dist_dir / 'quickstart.sh', 0o755)

    print("\nProject packaged successfully!")
    print(f"Deployment package created in: {dist_dir}")
    print("\nTo deploy on a new server:")
    print("1. Copy the 'dist/cernoid' directory to the target server")
    print("2. Navigate to the directory")
    print("3. Run './quickstart.sh'")
    print("4. Follow the prompts to complete setup")

if __name__ == '__main__':
    package_project() 