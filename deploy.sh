#!/bin/bash
set -e

# This script runs on the Lightsail server to deploy the app

echo "🚀 Starting deployment..."

# Navigate to application directory
cd /opt/expense-tracker

# Export environment variables explicitly
export DOCKER_IMAGE="${DOCKER_IMAGE}"
export POSTGRES_HOST="${POSTGRES_HOST}"
export POSTGRES_PORT="${POSTGRES_PORT}"
export POSTGRES_DB="${POSTGRES_DB}"
export POSTGRES_USER="${POSTGRES_USER}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
export OPENAI_API_KEY="${OPENAI_API_KEY}"

# Create .env file with environment variables as backup
cat > .env << EOF
DOCKER_IMAGE=${DOCKER_IMAGE}
POSTGRES_HOST=${POSTGRES_HOST}
POSTGRES_PORT=${POSTGRES_PORT}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
OPENAI_API_KEY=${OPENAI_API_KEY}
FX_PRIMARY=coingecko
ARS_SOURCE=blue
EOF

echo "✅ Environment variables exported and .env file created"

# Debug: Show that variables are set
echo "🔍 Verifying environment variables:"
echo "   DOCKER_IMAGE: ${DOCKER_IMAGE:0:50}..."
echo "   POSTGRES_HOST: ${POSTGRES_HOST}"
echo "   TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:0:10}..."

# Check if Docker is installed and running
echo "🔍 Checking Docker installation..."
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker not found. Installing Docker..."

    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    rm get-docker.sh

    # Start Docker service
    sudo systemctl enable docker
    sudo systemctl start docker

    echo "✅ Docker installed successfully"
else
    echo "✅ Docker is already installed"
fi

# Ensure Docker service is running
if ! sudo systemctl is-active --quiet docker; then
    echo "🔄 Starting Docker service..."
    sudo systemctl start docker
fi

# Wait for Docker to be ready
echo "⏳ Waiting for Docker to be ready..."
for i in {1..30}; do
    # Try with sudo first since user might not be in docker group yet
    if sudo docker info >/dev/null 2>&1; then
        echo "✅ Docker is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Docker failed to start after 30 attempts"
        # Show docker service status for debugging
        sudo systemctl status docker --no-pager || true
        exit 1
    fi
    sleep 2
done

# Since we might have just installed Docker, use sudo for docker commands
# or refresh group membership
if groups | grep -q docker; then
    echo "✅ User is in docker group"
    DOCKER_CMD="docker"
else
    echo "⚠️  User not in docker group yet, using sudo"
    DOCKER_CMD="sudo docker"
fi

# Log in to GitHub Container Registry
echo "${GITHUB_TOKEN}" | ${DOCKER_CMD} login ghcr.io -u "${GITHUB_ACTOR}" --password-stdin

echo "✅ Logged in to container registry"

# Check which docker compose command is available
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
elif groups | grep -q docker; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="sudo docker compose"
fi

echo "Using Docker Compose command: ${DOCKER_COMPOSE}"

# Pull the new image
${DOCKER_COMPOSE} pull

echo "✅ Pulled new image"

# Stop and remove old containers
${DOCKER_COMPOSE} down || true

# Start new containers
${DOCKER_COMPOSE} up -d

echo "✅ Started containers"

# Wait for health check
echo "⏳ Waiting for application to be healthy..."
for i in {1..30}; do
  if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Application is healthy!"
    break
  fi
  echo "   Waiting for application... ($i/30)"
  sleep 10
done

# Cleanup old images
${DOCKER_CMD} image prune -f

echo "🎉 Deployment completed successfully!"
