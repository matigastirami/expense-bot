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

# Pull the new image
docker compose pull

echo "✅ Pulled new image"

# Stop and remove old containers
docker compose down || true

# Start new containers
docker compose up -d

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
