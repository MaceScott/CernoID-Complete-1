#!/usr/bin/env python3
"""
Deployment script for CernoID
"""
import argparse
import subprocess
import os
import sys
from pathlib import Path

def check_prerequisites():
    """Check if required tools are installed"""
    required_tools = ['docker', 'docker-compose', 'git']
    
    for tool in required_tools:
        if subprocess.call(['which', tool], stdout=subprocess.DEVNULL) != 0:
            print(f"Error: {tool} is not installed")
            sys.exit(1)

def setup_environment():
    """Set up environment variables"""
    if not Path('.env').exists():
        print("Creating .env file from template")
        subprocess.run(['cp', '.env.example', '.env'])
        print("Please edit .env file with your configuration")
        sys.exit(1)

def build_and_deploy():
    """Build and deploy the application"""
    try:
        # Build containers
        subprocess.run(['docker-compose', 'build'], check=True)
        
        # Start services
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        
        print("Deployment successful!")
        
    except subprocess.CalledProcessError as e:
        print(f"Deployment failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Deploy CernoID')
    parser.add_argument('--env', choices=['prod', 'staging', 'dev'],
                      default='prod', help='Deployment environment')
    
    args = parser.parse_args()
    
    print(f"Deploying to {args.env} environment")
    
    # Ensure we're in the correct directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    check_prerequisites()
    setup_environment()
    build_and_deploy()

if __name__ == '__main__':
    main() 