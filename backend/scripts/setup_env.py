#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

def load_example_env() -> Dict[str, Any]:
    """Load example environment variables from .env.example"""
    example_path = Path(__file__).parent.parent / ".env.example"
    if not example_path.exists():
        print("Error: .env.example file not found")
        sys.exit(1)
        
    with open(example_path) as f:
        return {line.split("=")[0]: line.split("=")[1].strip() 
                for line in f if line.strip() and not line.startswith("#")}

def create_env_file(env_vars: Dict[str, Any], force: bool = False) -> None:
    """Create .env file with environment variables"""
    env_path = Path(__file__).parent.parent / ".env"
    
    if env_path.exists() and not force:
        print(f"Warning: {env_path} already exists. Use --force to overwrite.")
        return
        
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
            
    print(f"Created {env_path}")

def validate_env_file() -> bool:
    """Validate the .env file using the validation module"""
    try:
        from src.core.config.validate import validate_env
        result = validate_env()
        if result["success"]:
            print("Environment validation successful")
            return True
        else:
            print("Environment validation failed:")
            print(result["error"])
            return False
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        return False

def main():
    """Main function to set up environment variables"""
    import argparse
    parser = argparse.ArgumentParser(description="Set up environment variables for development")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing .env file")
    args = parser.parse_args()
    
    # Load example environment variables
    env_vars = load_example_env()
    
    # Create .env file
    create_env_file(env_vars, args.force)
    
    # Validate environment
    if validate_env_file():
        print("\nEnvironment setup complete!")
        print("\nNext steps:")
        print("1. Review the generated .env file")
        print("2. Update any sensitive values (passwords, API keys, etc.)")
        print("3. Start the development server")
    else:
        print("\nEnvironment setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 