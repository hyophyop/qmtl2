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
    uv venv create .venv
fi
uv pip install -e ".[dev]"

# Pull and build Docker images used for tests
sudo docker-compose -f docker-compose.dev.yml pull --ignore-pull-failures
sudo docker-compose -f docker-compose.dev.yml build

echo "[INFO] Environment prepared. Docker images and Python deps are cached for offline use."
