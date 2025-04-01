#!/bin/bash

# Exit on any error
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists python3; then
    echo "Python 3 is not installed"
    exit 1
fi

if ! command_exists node; then
    echo "Node.js is not installed"
    exit 1
fi

if ! command_exists docker; then
    echo "Docker is not installed"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "Docker Compose is not installed"
    exit 1
fi

if ! command_exists poetry; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

if ! command_exists pre-commit; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Set up backend
echo "Setting up backend..."
cd backend
poetry install
poetry run pre-commit install

# Set up frontend
echo "Setting up frontend..."
cd ../frontend
npm install

# Set up Vault
echo "Setting up Vault..."
cd ..
./scripts/setup_vault.sh

# Create development environment file
echo "Creating development environment file..."
cat > .env << EOF
# Development environment configuration
ENVIRONMENT=development
DEBUG=true

# Service URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
VAULT_URL=http://localhost:8200

# Development settings
NODE_ENV=development
PYTHONPATH=backend/src
PYTHONUNBUFFERED=1

# Docker settings
COMPOSE_PROJECT_NAME=cernoid_dev
EOF

# Create data directories
echo "Creating data directories..."
mkdir -p data/logs data/models

echo "Development environment setup complete!"
echo "You can now start the development environment with:"
echo "  docker-compose up -d"
echo "  cd backend && poetry run uvicorn src.main:app --reload"
echo "  cd frontend && npm run dev" 