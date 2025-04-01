#!/usr/bin/env python3
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from backend.app.core.secrets import SecretsManager

def load_env_file(file_path: str) -> Dict[str, str]:
    """Load environment variables from a .env file"""
    env_vars = {}
    load_dotenv(file_path)
    for key, value in os.environ.items():
        env_vars[key] = value
    return env_vars

def save_env_file(env_vars: Dict[str, str], file_path: str) -> None:
    """Save environment variables to a .env file"""
    with open(file_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

def validate_env_vars(env_vars: Dict[str, str], required_vars: List[str]) -> List[str]:
    """Validate required environment variables"""
    missing = []
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            missing.append(var)
    return missing

def encrypt_secrets(env_vars: Dict[str, str], secrets_manager: SecretsManager) -> Dict[str, str]:
    """Encrypt sensitive environment variables"""
    sensitive_vars = [
        'DB_PASSWORD',
        'REDIS_PASSWORD',
        'JWT_SECRET',
        'SECRET_KEY',
        'SMTP_PASSWORD',
        'GRAFANA_ADMIN_PASSWORD'
    ]
    
    for var in sensitive_vars:
        if var in env_vars and env_vars[var]:
            env_vars[var] = secrets_manager.encrypt(env_vars[var])
    
    return env_vars

def decrypt_secrets(env_vars: Dict[str, str], secrets_manager: SecretsManager) -> Dict[str, str]:
    """Decrypt sensitive environment variables"""
    sensitive_vars = [
        'DB_PASSWORD',
        'REDIS_PASSWORD',
        'JWT_SECRET',
        'SECRET_KEY',
        'SMTP_PASSWORD',
        'GRAFANA_ADMIN_PASSWORD'
    ]
    
    for var in sensitive_vars:
        if var in env_vars and env_vars[var]:
            try:
                env_vars[var] = secrets_manager.decrypt(env_vars[var])
            except Exception:
                print(f"Warning: Could not decrypt {var}")
    
    return env_vars

def main():
    parser = argparse.ArgumentParser(description='Manage environment variables')
    parser.add_argument('--init', action='store_true', help='Initialize environment files')
    parser.add_argument('--validate', action='store_true', help='Validate environment variables')
    parser.add_argument('--encrypt', action='store_true', help='Encrypt sensitive variables')
    parser.add_argument('--decrypt', action='store_true', help='Decrypt sensitive variables')
    parser.add_argument('--export', action='store_true', help='Export environment variables')
    parser.add_argument('--import', dest='import_file', help='Import environment variables from file')
    parser.add_argument('--env', default='development', choices=['development', 'production'], help='Environment to manage')
    
    args = parser.parse_args()
    
    # Initialize paths
    root_dir = Path(__file__).parent.parent
    env_dir = root_dir / 'config' / 'env'
    env_dir.mkdir(parents=True, exist_ok=True)
    
    # Load example environment
    example_env = load_env_file(root_dir / '.env.example')
    
    if args.init:
        # Create environment files
        env_files = {
            'frontend': root_dir / 'frontend' / '.env',
            'backend': root_dir / 'backend' / '.env',
            'root': root_dir / '.env'
        }
        
        for name, path in env_files.items():
            if not path.exists():
                save_env_file(example_env, path)
                print(f"Created {name} environment file")
    
    if args.validate:
        # Validate environment variables
        required_vars = [
            'DB_USER',
            'DB_PASSWORD',
            'DB_NAME',
            'REDIS_PASSWORD',
            'JWT_SECRET',
            'SECRET_KEY'
        ]
        
        env_vars = load_env_file(root_dir / '.env')
        missing = validate_env_vars(env_vars, required_vars)
        
        if missing:
            print("Missing required environment variables:")
            for var in missing:
                print(f"  - {var}")
            sys.exit(1)
        else:
            print("All required environment variables are set")
    
    if args.encrypt or args.decrypt:
        secrets_manager = SecretsManager()
        
        # Process all environment files
        env_files = [
            root_dir / 'frontend' / '.env',
            root_dir / 'backend' / '.env',
            root_dir / '.env'
        ]
        
        for path in env_files:
            if path.exists():
                env_vars = load_env_file(path)
                if args.encrypt:
                    env_vars = encrypt_secrets(env_vars, secrets_manager)
                else:
                    env_vars = decrypt_secrets(env_vars, secrets_manager)
                save_env_file(env_vars, path)
                print(f"Processed {path}")
    
    if args.export:
        # Export environment variables
        env_vars = load_env_file(root_dir / '.env')
        output_file = env_dir / f'{args.env}_env.json'
        
        with open(output_file, 'w') as f:
            json.dump(env_vars, f, indent=2)
        print(f"Exported environment variables to {output_file}")
    
    if args.import_file:
        # Import environment variables
        with open(args.import_file) as f:
            env_vars = json.load(f)
        
        save_env_file(env_vars, root_dir / '.env')
        print(f"Imported environment variables from {args.import_file}")

if __name__ == '__main__':
    main() 