#!/bin/bash
# Setup script for Codex offline environment
# Installs dependencies and pulls Docker images so they are available offline.
set -e

# Install system packages
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip docker.io docker-compose

# Install uv package manager if not present
if ! command -v uv >/dev/null 2>&1; then
    sudo pip3 install uv
fi

# Create venv and install project dependencies including dev extras
if [ ! -d ".venv" ]; then
    uv venv .venv
fi
uv pip install -e ".[dev]"

# Check if Docker service is running
if ! sudo systemctl is-active --quiet docker; then
    echo "[INFO] Docker service is not running. Starting Docker..."
    sudo systemctl start docker
    sleep 3  # Give Docker a moment to start properly
fi

# Add current user to docker group to avoid permission issues
if ! groups | grep -q "\bdocker\b"; then
    echo "[INFO] Adding $(whoami) to the docker group..."
    sudo usermod -aG docker $(whoami)
    echo "[WARN] You might need to log out and log back in for group changes to take effect."
    echo "[WARN] If the script fails after this point, please log out, log back in, and run it again."
fi

# Check if Docker is accessible
if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker is not accessible. Please ensure Docker is running and you have necessary permissions."
    echo "[INFO] You can try: sudo systemctl start docker"
    echo "[INFO] And ensure your user is in the docker group: sudo usermod -aG docker \$(whoami)"
    exit 1
fi

# Pull and build Docker images used for tests
sudo docker-compose -f docker-compose.dev.yml pull --ignore-pull-failures
sudo docker-compose -f docker-compose.dev.yml build

echo "[INFO] Environment prepared. Docker images and Python deps are cached for offline use."
