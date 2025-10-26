#!/bin/bash

# Simple script to run migrations inside the running API container
# Run this AFTER deploy.sh has started the containers

echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T api sh -c "cd /app && alembic upgrade head"

if [ $? -eq 0 ]; then
    echo "✓ Migrations completed successfully"
else
    echo "✗ Migrations failed"
    exit 1
fi
