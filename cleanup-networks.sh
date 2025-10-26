#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Docker Network Cleanup${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Stop all containers first
echo -e "${YELLOW}Stopping all expense tracker containers...${NC}"
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
echo ""

# List all networks related to the project
echo -e "${YELLOW}Finding related Docker networks...${NC}"
networks=$(docker network ls --filter "name=expense" --format "{{.Name}}")

if [ -z "$networks" ]; then
    echo -e "${GREEN}No expense tracker networks found.${NC}"
else
    echo "Found the following networks:"
    echo "$networks"
    echo ""

    # Remove each network
    echo -e "${YELLOW}Removing networks...${NC}"
    for network in $networks; do
        echo "Removing network: $network"
        docker network rm "$network" 2>/dev/null || echo "  (already removed or in use)"
    done
fi

echo ""
echo -e "${GREEN}✓ Network cleanup complete${NC}"
echo ""
echo "You can now run: ./deploy.sh"
