#!/bin/bash
set -e

# This script runs on the Lightsail server to deploy the app

echo "🚀 Starting deployment..."

# Navigate to application directory
cd /opt/expense-tracker

# Create .env file with environment variables
cat > .env << 'EOF'
DOCKER_IMAGE=${DOCKER_IMAGE}
POSTGRES_HOST=${POSTGRES_HOST}
POSTGRES_PORT=${POSTGRES_PORT}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
OPENAI_API_KEY=${OPENAI_API_KEY}
EOF

echo "✅ Environment file created"

# Log in to GitHub Container Registry
echo "${GITHUB_TOKEN}" | docker login ghcr.io -u "${GITHUB_ACTOR}" --password-stdin

echo "✅ Logged in to container registry"

# Check which docker compose command is available
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
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
docker image prune -f

echo "🎉 Deployment completed successfully!"
