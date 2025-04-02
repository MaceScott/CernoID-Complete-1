#!/bin/bash

# Exit on error
set -e

# Check if Vault is installed
if ! command -v vault &> /dev/null; then
    echo "Error: HashiCorp Vault is not installed"
    echo "Please install Vault from https://www.vaultproject.io/docs/install"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running"
    exit 1
fi

# Create necessary directories
mkdir -p deployment/vault/config
mkdir -p deployment/vault/data
mkdir -p deployment/vault/logs

# Create Vault configuration file
cat > deployment/vault/config/vault.json << EOF
{
  "backend": {
    "file": {
      "path": "/vault/data"
    }
  },
  "listener": {
    "tcp": {
      "address": "0.0.0.0:8200",
      "tls_disable": 1
    }
  },
  "ui": true,
  "disable_mlock": true
}
EOF

# Create Vault service in docker-compose
cat > deployment/vault/docker-compose.yml << EOF
version: '3.8'

services:
  vault:
    image: hashicorp/vault:latest
    container_name: cernoid-vault
    ports:
      - "8200:8200"
    volumes:
      - ./config:/vault/config
      - ./data:/vault/data
      - ./logs:/vault/logs
    environment:
      - VAULT_ADDR=http://0.0.0.0:8200
    cap_add:
      - IPC_LOCK
    restart: unless-stopped
EOF

# Start Vault container
cd deployment/vault
docker-compose up -d

# Wait for Vault to start
echo "Waiting for Vault to start..."
sleep 5

# Initialize Vault
echo "Initializing Vault..."
INIT_OUTPUT=$(vault operator init -key-shares=5 -key-threshold=3 -format=json)

# Extract unseal keys and root token
UNSEAL_KEY_1=$(echo $INIT_OUTPUT | jq -r '.unseal_keys_b64[0]')
UNSEAL_KEY_2=$(echo $INIT_OUTPUT | jq -r '.unseal_keys_b64[1]')
UNSEAL_KEY_3=$(echo $INIT_OUTPUT | jq -r '.unseal_keys_b64[2]')
ROOT_TOKEN=$(echo $INIT_OUTPUT | jq -r '.root_token')

# Unseal Vault
echo "Unsealing Vault..."
vault operator unseal $UNSEAL_KEY_1
vault operator unseal $UNSEAL_KEY_2
vault operator unseal $UNSEAL_KEY_3

# Enable KV secrets engine
echo "Configuring Vault..."
vault secrets enable -version=2 kv

# Create policies
echo "Creating Vault policies..."

# Admin policy
cat > admin-policy.hcl << EOF
path "auth/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "kv/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

# App policy
cat > app-policy.hcl << EOF
path "kv/data/cernoid/*" {
  capabilities = ["read"]
}

path "kv/data/cernoid/{{identity.entity.name}}/*" {
  capabilities = ["create", "read", "update", "delete"]
}
EOF

# Write policies
vault policy write admin admin-policy.hcl
vault policy write app app-policy.hcl

# Create tokens
echo "Creating Vault tokens..."

# Admin token
ADMIN_TOKEN=$(vault token create -policy=admin -format=json | jq -r '.auth.client_token')

# App token
APP_TOKEN=$(vault token create -policy=app -format=json | jq -r '.auth.client_token')

# Save tokens and keys securely
echo "Saving Vault credentials..."
mkdir -p ../../config/vault
cat > ../../config/vault/credentials.json << EOF
{
  "root_token": "$ROOT_TOKEN",
  "unseal_keys": [
    "$UNSEAL_KEY_1",
    "$UNSEAL_KEY_2",
    "$UNSEAL_KEY_3"
  ],
  "admin_token": "$ADMIN_TOKEN",
  "app_token": "$APP_TOKEN"
}
EOF

# Set file permissions
chmod 600 ../../config/vault/credentials.json

# Update .env file with Vault configuration
echo "Updating environment configuration..."
cat >> ../../.env << EOF

# Vault Configuration
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=$APP_TOKEN
VAULT_PATH=kv/data/cernoid
EOF

echo "Vault setup completed successfully!"
echo "Please save the following information securely:"
echo "Root Token: $ROOT_TOKEN"
echo "Admin Token: $ADMIN_TOKEN"
echo "App Token: $APP_TOKEN"
echo "Unseal Keys:"
echo "$UNSEAL_KEY_1"
echo "$UNSEAL_KEY_2"
echo "$UNSEAL_KEY_3"
echo ""
echo "These credentials are also saved in config/vault/credentials.json"
echo "Make sure to keep this file secure and never commit it to version control." 