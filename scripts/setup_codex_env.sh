#!/bin/bash
# Setup script for Codex offline environment
# Installs dependencies and pulls Docker images so they are available offline.
set -e

# Function to check if we're on macOS
is_macos() {
  [[ "$(uname -s)" == "Darwin" ]] && return 0 || return 1
}

# Function to check if we're in a container or WSL1
is_container_or_wsl1() {
  if [ -f /proc/1/cgroup ] && grep -q "docker\|lxc" /proc/1/cgroup; then
    return 0
  elif uname -r | grep -q "Microsoft"; then
    if [ ! -d /sys/fs/cgroup/systemd ]; then
      return 0 # WSL1
    fi
  fi
  return 1
}

# Install system packages (on Linux only)
if ! is_macos; then
  if command -v apt-get >/dev/null 2>&1; then
    echo "[INFO] Installing system packages using apt-get..."
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip
    
    # Install Docker if not already present
    if ! command -v docker >/dev/null 2>&1; then
      echo "[INFO] Installing Docker..."
      sudo apt-get install -y docker.io docker-compose
    fi
  elif command -v yum >/dev/null 2>&1; then
    echo "[INFO] Installing system packages using yum..."
    sudo yum update -y
    sudo yum install -y python3-pip
    
    # Install Docker if not already present
    if ! command -v docker >/dev/null 2>&1; then
      echo "[INFO] Installing Docker..."
      sudo yum install -y docker docker-compose
    fi
  fi
fi

# Install uv package manager if not present
if ! command -v uv >/dev/null 2>&1; then
    echo "[INFO] Installing uv package manager..."
    pip3 install --user uv || sudo pip3 install uv
fi

# Create venv and install project dependencies including dev extras
if [ ! -d ".venv" ]; then
    echo "[INFO] Creating Python virtual environment..."
    uv venv .venv
fi
echo "[INFO] Installing project dependencies..."
uv pip install -e ".[dev]"

# Start Docker service based on environment
if command -v docker >/dev/null 2>&1; then
    echo "[INFO] Checking Docker status..."
    
    if is_macos; then
        # On macOS, check if Docker Desktop is running
        if ! docker info >/dev/null 2>&1; then
            echo "[WARN] Docker Desktop doesn't seem to be running on macOS."
            echo "[WARN] Please start Docker Desktop manually and run this script again."
            exit 1
        fi
    elif ! is_container_or_wsl1; then
        # On Linux with systemd
        if command -v systemctl >/dev/null 2>&1; then
            if ! systemctl is-active --quiet docker; then
                echo "[INFO] Starting Docker service via systemd..."
                sudo systemctl start docker
                sleep 3
            fi
        else
            # On Linux without systemd
            if ! ps aux | grep -v grep | grep -q dockerd; then
                echo "[INFO] Starting Docker service..."
                sudo service docker start 2>/dev/null || sudo /etc/init.d/docker start 2>/dev/null || echo "[WARN] Could not start Docker service automatically."
                sleep 3
            fi
        fi
    else
        echo "[INFO] Running in container or WSL1. Skipping Docker service management."
    fi

    # Check if Docker is accessible
    if ! docker info >/dev/null 2>&1; then
        echo "[ERROR] Docker is not accessible. Please ensure Docker is running and you have necessary permissions."
        echo "[INFO] If using Linux, ensure your user is in the docker group: sudo usermod -aG docker \$(whoami)"
        echo "[INFO] Then log out and log back in, or run: newgrp docker"
        echo "[INFO] If using macOS, ensure Docker Desktop is running."
        exit 1
    fi

    # Pull and build Docker images used for tests
    echo "[INFO] Pulling and building Docker images..."
    if is_container_or_wsl1; then
        echo "[WARN] Running in container or WSL1 environment. Docker operations might require special handling."
    fi
    
    if [ -f "docker-compose.dev.yml" ]; then
        docker-compose -f docker-compose.dev.yml pull --ignore-pull-failures || sudo docker-compose -f docker-compose.dev.yml pull --ignore-pull-failures
        docker-compose -f docker-compose.dev.yml build || sudo docker-compose -f docker-compose.dev.yml build
    else
        echo "[WARN] docker-compose.dev.yml not found in current directory. Skipping Docker images."
    fi
else
    echo "[WARN] Docker not installed. Skipping Docker setup steps."
fi

echo "[INFO] Environment prepared. Python dependencies are installed."
if command -v docker >/dev/null 2>&1; then
    echo "[INFO] Docker images are cached for offline use."
fi
