def create_docker_requirements():
    """Create Docker-specific requirements file"""
    windows_packages = [
        'pywin32',
        'pywinpty',
        'win32-setctime'
    ]

    with open('requirements.txt', 'r') as f:
        reqs = f.readlines()

    # Filter out Windows-specific packages
    docker_reqs = [
        req for req in reqs 
        if not any(pkg in req.lower() for pkg in windows_packages)
    ]

    # Write Docker requirements
    with open('requirements.docker.txt', 'w') as f:
        f.writelines(docker_reqs)

if __name__ == '__main__':
    create_docker_requirements() 