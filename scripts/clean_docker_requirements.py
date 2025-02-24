def clean_docker_requirements():
    """Create Docker-compatible requirements file"""
    # Windows-specific packages to remove
    windows_packages = {
        'pywin32',
        'pywinpty',
        'win32-setctime',
        'wincertstore',
        'winpty',
        'pypiwin32'
    }

    print("Creating Docker-compatible requirements...")
    
    try:
        # Read current requirements
        with open('requirements.txt', 'r') as f:
            reqs = [line.strip() for line in f.readlines() if line.strip()]

        # Filter out Windows packages and empty lines
        docker_reqs = []
        removed_reqs = []
        
        for req in reqs:
            # Skip comments and empty lines
            if req.startswith('#') or not req:
                continue
                
            # Check if it's a Windows package
            if any(wp.lower() in req.lower() for wp in windows_packages):
                removed_reqs.append(req)
                continue
                
            docker_reqs.append(req)

        # Write Docker requirements
        with open('requirements.docker.txt', 'w') as f:
            f.write('\n'.join(docker_reqs))
            
        print("\nCreated requirements.docker.txt")
        print(f"Removed {len(removed_reqs)} Windows-specific packages:")
        for req in removed_reqs:
            print(f"- {req}")
            
        print("\nRemaining packages:", len(docker_reqs))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    clean_docker_requirements() 