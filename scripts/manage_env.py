#!/usr/bin/env python3
import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from cryptography.fernet import Fernet
import hvac
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Sensitive variables that should be encrypted
SENSITIVE_VARS = [
    'DB_PASSWORD',
    'REDIS_PASSWORD',
    'JWT_SECRET',
    'SECRET_KEY',
    'SMTP_PASSWORD',
    'GRAFANA_ADMIN_PASSWORD',
    'NEXTAUTH_SECRET'
]

def setup_vault_client() -> Optional[hvac.Client]:
    """Set up HashiCorp Vault client."""
    try:
        client = hvac.Client(
            url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
            token=os.getenv('VAULT_TOKEN')
        )
        if not client.is_authenticated():
            print("Warning: Vault authentication failed")
            return None
        return client
    except Exception as e:
        print(f"Warning: Failed to connect to Vault: {e}")
        return None

def generate_key() -> bytes:
    """Generate a new Fernet key for encryption."""
    return Fernet.generate_key()

def load_key() -> Optional[bytes]:
    """Load the encryption key from file."""
    key_path = Path('.secrets.key')
    if key_path.exists():
        with open(key_path, 'rb') as f:
            return f.read()
    return None

def save_key(key: bytes):
    """Save the encryption key to file."""
    with open('.secrets.key', 'wb') as f:
        f.write(key)

def encrypt_value(value: str, key: bytes) -> str:
    """Encrypt a value using Fernet."""
    f = Fernet(key)
    return f.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str, key: bytes) -> str:
    """Decrypt a value using Fernet."""
    f = Fernet(key)
    return f.decrypt(encrypted_value.encode()).decode()

def read_env_file(file_path: str) -> Dict[str, str]:
    """Read environment variables from a file."""
    env_vars = {}
    env_path = Path(file_path)
    
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
                    except ValueError:
                        continue
    
    return env_vars

def write_env_file(env_vars: Dict[str, str], file_path: str):
    """Write environment variables to a file."""
    with open(file_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

def sync_with_vault(env_vars: Dict[str, str], client: hvac.Client):
    """Sync sensitive variables with Vault."""
    if not client:
        return
    
    try:
        # Read existing secrets from Vault
        try:
            response = client.secrets.kv.v2.read_secret_version(
                path=os.getenv('VAULT_PATH', 'secret/cernoid')
            )
            vault_secrets = response['data']['data']
        except:
            vault_secrets = {}
        
        # Update Vault with new sensitive variables
        for var in SENSITIVE_VARS:
            if var in env_vars:
                vault_secrets[var] = env_vars[var]
        
        # Write updated secrets back to Vault
        client.secrets.kv.v2.create_or_update_secret(
            path=os.getenv('VAULT_PATH', 'secret/cernoid'),
            secret=vault_secrets
        )
    except Exception as e:
        print(f"Warning: Failed to sync with Vault: {e}")

def init_env(args):
    """Initialize environment files."""
    # Copy example files if they don't exist
    example_files = {
        '.env.example': '.env',
        'frontend/.env.example': 'frontend/.env',
        'backend/.env.example': 'backend/.env'
    }
    
    for example, target in example_files.items():
        if not Path(target).exists():
            subprocess.run(['cp', example, target])
            print(f"Created {target} from {example}")
    
    # Generate encryption key if it doesn't exist
    if not load_key():
        key = generate_key()
        save_key(key)
        print("Generated new encryption key")

def validate_env(args):
    """Validate environment variables."""
    subprocess.run([sys.executable, 'scripts/validate_env.py'])

def encrypt_env(args):
    """Encrypt sensitive environment variables."""
    key = load_key()
    if not key:
        print("Error: No encryption key found")
        sys.exit(1)
    
    env_files = ['.env', 'frontend/.env', 'backend/.env']
    for env_file in env_files:
        env_vars = read_env_file(env_file)
        for var in SENSITIVE_VARS:
            if var in env_vars:
                env_vars[var] = encrypt_value(env_vars[var], key)
        write_env_file(env_vars, env_file)
        print(f"Encrypted sensitive variables in {env_file}")

def decrypt_env(args):
    """Decrypt sensitive environment variables."""
    key = load_key()
    if not key:
        print("Error: No encryption key found")
        sys.exit(1)
    
    env_files = ['.env', 'frontend/.env', 'backend/.env']
    for env_file in env_files:
        env_vars = read_env_file(env_file)
        for var in SENSITIVE_VARS:
            if var in env_vars:
                try:
                    env_vars[var] = decrypt_value(env_vars[var], key)
                except:
                    print(f"Warning: Failed to decrypt {var} in {env_file}")
        write_env_file(env_vars, env_file)
        print(f"Decrypted sensitive variables in {env_file}")

def sync_vault(args):
    """Sync environment variables with Vault."""
    client = setup_vault_client()
    if not client:
        print("Error: Failed to connect to Vault")
        sys.exit(1)
    
    env_vars = read_env_file('.env')
    sync_with_vault(env_vars, client)
    print("Synced environment variables with Vault")

def export_env(args):
    """Export environment variables to a file."""
    env_vars = read_env_file('.env')
    output_file = args.output or f"config/env/{args.env}_env.json"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(env_vars, f, indent=2)
    print(f"Exported environment variables to {output_file}")

def import_env(args):
    """Import environment variables from a file."""
    input_file = args.input or f"config/env/{args.env}_env.json"
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    with open(input_file) as f:
        env_vars = json.load(f)
    
    write_env_file(env_vars, '.env')
    print(f"Imported environment variables from {input_file}")

def main():
    parser = argparse.ArgumentParser(description='Manage environment variables')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Initialize environment
    subparsers.add_parser('init', help='Initialize environment files')
    
    # Validate environment
    subparsers.add_parser('validate', help='Validate environment variables')
    
    # Encrypt environment
    subparsers.add_parser('encrypt', help='Encrypt sensitive variables')
    
    # Decrypt environment
    subparsers.add_parser('decrypt', help='Decrypt sensitive variables')
    
    # Sync with Vault
    subparsers.add_parser('sync-vault', help='Sync with Vault')
    
    # Export environment
    export_parser = subparsers.add_parser('export', help='Export environment variables')
    export_parser.add_argument('--env', default='development', help='Environment name')
    export_parser.add_argument('--output', help='Output file path')
    
    # Import environment
    import_parser = subparsers.add_parser('import', help='Import environment variables')
    import_parser.add_argument('--env', default='development', help='Environment name')
    import_parser.add_argument('--input', help='Input file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        'init': init_env,
        'validate': validate_env,
        'encrypt': encrypt_env,
        'decrypt': decrypt_env,
        'sync-vault': sync_vault,
        'export': export_env,
        'import': import_env
    }
    
    commands[args.command](args)

if __name__ == "__main__":
    main() 