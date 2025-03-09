#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to print messages
echo_message() {
    echo "[INSTALL] $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check and install Docker if needed
install_docker() {
    if ! command_exists docker; then
        echo_message "Docker not found. Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
    else
        echo_message "Docker is already installed"
    fi
}

# Check and install Docker Compose if needed
install_docker_compose() {
    if ! command_exists docker-compose; then
        echo_message "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        echo_message "Docker Compose is already installed"
    fi
}

# Main installation process
main() {
    echo_message "Starting CernoID installation..."

    # Install Docker and Docker Compose
    install_docker
    install_docker_compose

    # Create necessary directories
    echo_message "Creating required directories..."
    mkdir -p ./data/db
    mkdir -p ./data/redis
    mkdir -p ./logs

    # Set up environment variables
    echo_message "Setting up environment variables..."
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo_message "Created .env file from template. Please update with your settings."
    fi

    # Pull and start containers
    echo_message "Starting services..."
    docker-compose pull
    docker-compose up -d

    # Wait for services to be healthy
    echo_message "Waiting for services to be ready..."
    sleep 30

    echo_message "Installation complete!"
    echo_message "Frontend available at: http://localhost:3000"
    echo_message "Backend API available at: http://localhost:8000"
}

# Run main installation
main "$@" 