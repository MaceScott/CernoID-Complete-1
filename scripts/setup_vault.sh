#!/bin/bash

# Exit on any error
set -e

# Function to check if Vault is ready
check_vault() {
    local max_retries=30
    local retry_count=1
    
    echo "Checking Vault status..."
    while [ $retry_count -le $max_retries ]; do
        if curl -s http://localhost:8200/v1/sys/health > /dev/null; then
            echo "Vault is ready"
            return 0
        fi
        echo "Waiting for Vault to be ready (attempt $retry_count/$max_retries)..."
        sleep 2
        retry_count=$((retry_count + 1))
    done
    echo "Vault is not ready after $max_retries attempts"
    return 1
}

# Start Vault if not running
if ! docker-compose ps | grep -q "vault.*running"; then
    echo "Starting Vault..."
    docker-compose up -d vault
    sleep 5
fi

# Wait for Vault to be ready
check_vault

# Initialize Vault if not already initialized
if ! docker-compose exec -T vault vault status > /dev/null 2>&1; then
    echo "Initializing Vault..."
    docker-compose exec -T vault vault operator init > vault_init.txt
    
    # Extract root token and unseal keys
    ROOT_TOKEN=$(grep 'Initial Root Token:' vault_init.txt | awk '{print $NF}')
    UNSEAL_KEY_1=$(grep 'Unseal Key 1:' vault_init.txt | awk '{print $NF}')
    UNSEAL_KEY_2=$(grep 'Unseal Key 2:' vault_init.txt | awk '{print $NF}')
    UNSEAL_KEY_3=$(grep 'Unseal Key 3:' vault_init.txt | awk '{print $NF}')
    
    # Store keys securely
    mkdir -p .vault
    echo "$ROOT_TOKEN" > .vault/root_token
    echo "$UNSEAL_KEY_1" > .vault/unseal_key_1
    echo "$UNSEAL_KEY_2" > .vault/unseal_key_2
    echo "$UNSEAL_KEY_3" > .vault/unseal_key_3
    chmod 600 .vault/*
    
    # Unseal Vault
    echo "Unsealing Vault..."
    docker-compose exec -T vault vault operator unseal "$UNSEAL_KEY_1"
    docker-compose exec -T vault vault operator unseal "$UNSEAL_KEY_2"
    docker-compose exec -T vault vault operator unseal "$UNSEAL_KEY_3"
fi

# Login to Vault
echo "Logging in to Vault..."
ROOT_TOKEN=$(cat .vault/root_token)
docker-compose exec -T vault vault login "$ROOT_TOKEN"

# Enable secrets engine
echo "Enabling secrets engine..."
docker-compose exec -T vault vault secrets enable -path=cernoid kv-v2 || true

# Store secrets
echo "Storing secrets..."
docker-compose exec -T vault vault kv put cernoid/database \
    url="postgresql://postgres:postgres@db:5432/cernoid" \
    username="postgres" \
    password="postgres"

docker-compose exec -T vault vault kv put cernoid/redis \
    url="redis://redis:6379" \
    host="redis" \
    port="6379" \
    db="0"

docker-compose exec -T vault vault kv put cernoid/jwt \
    secret="$(openssl rand -base64 32)"

docker-compose exec -T vault vault kv put cernoid/cors \
    origin="http://localhost:3000" \
    allowed_origins="*"

# Create policy for services
echo "Creating service policy..."
cat > service-policy.hcl << EOF
path "cernoid/*" {
    capabilities = ["read"]
}
EOF

docker-compose exec -T vault vault policy write service-policy service-policy.hcl

# Create service token
echo "Creating service token..."
SERVICE_TOKEN=$(docker-compose exec -T vault vault token create \
    -policy=service-policy \
    -format=json | jq -r .auth.client_token)

# Store service token
echo "$SERVICE_TOKEN" > .vault/service_token
chmod 600 .vault/service_token

echo "Vault setup complete!"
echo "Service token stored in .vault/service_token"
echo "Root token and unseal keys stored in .vault/ directory" 