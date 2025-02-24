import re

def clean_requirements():
    """Remove Windows-specific packages and create Docker requirements"""
    windows_packages = [
        'pywin32',
        'pywinpty',
        'win32-setctime',
        'pypiwin32'
    ]

    print("Cleaning requirements for Docker...")
    
    try:
        # Read current requirements
        with open('requirements.txt', 'r') as f:
            reqs = f.readlines()

        # Filter out Windows packages
        docker_reqs = [
            req for req in reqs 
            if not any(pkg in req.lower() for pkg in windows_packages)
        ]

        # Write Docker requirements
        with open('requirements.docker.txt', 'w') as f:
            f.writelines(docker_reqs)
            
        print("Created requirements.docker.txt")
        print(f"Removed {len(reqs) - len(docker_reqs)} Windows-specific packages")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    clean_requirements() 