def fix_docker_requirements():
    """Create Docker-compatible requirements file"""
    import os
    
    print(f"Current directory: {os.getcwd()}")
    print("Creating Docker-compatible requirements...")
    
    try:
        # Read current requirements
        with open('requirements.txt', 'r') as f:
            reqs = [line.strip() for line in f.readlines() if line.strip()]

        # Windows packages to remove
        windows_packages = {
            'pywin32',
            'pywinpty',
            'win32-setctime',
            'pypiwin32',
            'wincertstore',
            'winpty',
            'pywin32-ctypes'
        }

        # Filter out Windows packages
        docker_reqs = []
        removed_reqs = []
        
        for req in reqs:
            if req.startswith('#') or not req:
                continue
            
            pkg_name = req.split('==')[0].lower()
            if any(wp in pkg_name for wp in windows_packages):
                removed_reqs.append(req)
            else:
                docker_reqs.append(req)

        # Write Docker requirements
        with open('requirements.docker.txt', 'w') as f:
            f.write('\n'.join(docker_reqs))
            
        print("\nCreated requirements.docker.txt")
        print(f"Removed {len(removed_reqs)} Windows-specific packages:")
        for req in removed_reqs:
            print(f"- {req}")
            
        print(f"\nRemaining packages: {len(docker_reqs)}")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error occurred in directory: {os.getcwd()}")

if __name__ == '__main__':
    fix_docker_requirements()
