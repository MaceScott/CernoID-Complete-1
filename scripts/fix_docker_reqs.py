def fix_docker_requirements():
    """Create Docker-compatible requirements file"""
    import os
    
    print("Creating Docker-compatible requirements...")
    
    try:
        # Read current requirements
        with open('requirements.txt', 'r') as f:
            reqs = [line.strip() for line in f.readlines() if line.strip()]

        # Windows packages to remove (exact matches)
        windows_packages = {
            'pywin32==308',
            'pywinpty==2.0.15',  # This needs Rust to compile
            'pywin32',
            'pywinpty',  # Remove base package too
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
            # Skip comments and empty lines
            if req.startswith('#') or not req:
                continue
            
            # Check for exact matches first
            if req in windows_packages:
                removed_reqs.append(req)
                print(f"Removing exact match: {req}")
                continue
                
            # Then check for partial matches
            if any(wp.split('==')[0] in req for wp in windows_packages):
                removed_reqs.append(req)
                print(f"Removing partial match: {req}")
                continue
                
            docker_reqs.append(req)

        # Write Docker requirements
        with open('requirements.docker.txt', 'w') as f:
            f.write('\n'.join(docker_reqs))
            
        print("\nCreated requirements.docker.txt")
        print(f"Removed {len(removed_reqs)} Windows-specific packages:")
        for req in removed_reqs:
            print(f"- {req}")
            
        print(f"\nRemaining packages: {len(docker_reqs)}")
        
        # Verify pywin32 is removed
        if any('pywin32' in req.lower() for req in docker_reqs):
            print("\nWARNING: pywin32 still found in requirements!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    fix_docker_requirements() 