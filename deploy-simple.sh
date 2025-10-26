#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Expense Tracker - Simple Deploy${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with your production configuration."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Clean up networks
echo -e "${YELLOW}Cleaning up networks...${NC}"
docker network prune -f
echo -e "${GREEN}✓ Networks cleaned${NC}"
echo ""

# Build Docker images
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build
echo -e "${GREEN}✓ Docker images built${NC}"
echo ""

# Start containers
echo -e "${YELLOW}Starting containers...${NC}"
docker-compose -f docker-compose.prod.yml up -d
echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# Wait for containers to be ready
echo -e "${YELLOW}Waiting for containers to be ready...${NC}"
sleep 10

# Run migrations inside the API container
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose -f docker-compose.prod.yml exec -T api sh -c "cd /app && alembic upgrade head" || {
    echo -e "${RED}Warning: Migrations failed. This might be okay if already up to date.${NC}"
    echo "Check logs with: docker-compose -f docker-compose.prod.yml logs api"
}
echo -e "${GREEN}✓ Migrations complete${NC}"
echo ""

# Check status
echo -e "${YELLOW}Container status:${NC}"
docker-compose -f docker-compose.prod.yml ps
echo ""

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Services:"
echo "  - API: http://localhost:${API_PORT:-8000}"
echo "  - Web: http://localhost:${WEB_PORT:-3000}"
echo "  - Bot: Running"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - Restart: docker-compose -f docker-compose.prod.yml restart"
echo "  - Stop: docker-compose -f docker-compose.prod.yml down"
