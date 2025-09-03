#!/bin/bash

# Startup script for Finance Agent
set -e

echo "🤖 Starting Finance Agent..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    echo "   cp .env.example .env"
    echo "   # Then edit .env with your API keys"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check for required environment variables
echo "🔍 Checking environment variables..."
source .env

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-..." ]; then
    echo "❌ Please set OPENAI_API_KEY in your .env file"
    exit 1
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "123:abc" ]; then
    echo "❌ Please set TELEGRAM_BOT_TOKEN in your .env file"
    exit 1
fi

echo "✅ Environment variables OK"

# Build Docker image if needed
echo "🔨 Building Docker image..."
docker build -t finance-agent . || {
    echo "❌ Docker build failed"
    exit 1
}

echo "✅ Docker image built successfully"

# Start services
echo "🚀 Starting services with docker-compose..."
docker-compose up -d postgres

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Run migrations
echo "📊 Running database migrations..."
docker-compose run --rm app alembic upgrade head || {
    echo "❌ Database migration failed"
    exit 1
}

echo "✅ Database migrations complete"

# Start the application
echo "🎯 Starting Finance Agent bot..."
docker-compose up app

echo "🎉 Finance Agent is now running!"
echo "📱 You can now interact with your bot on Telegram"