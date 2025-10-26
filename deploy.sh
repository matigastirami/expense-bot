#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Expense Tracker - Production Deploy${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with your production configuration."
    echo "You can copy .env.example and modify it: cp .env.example .env"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check required environment variables
required_vars=(
    "POSTGRES_HOST"
    "POSTGRES_DB"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "TELEGRAM_BOT_TOKEN"
    "OPENAI_API_KEY"
    "JWT_SECRET"
)

echo -e "${YELLOW}Checking required environment variables...${NC}"
missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}Error: Missing required environment variables:${NC}"
    for var in "${missing_vars[@]}"; do
        echo -e "  - $var"
    done
    exit 1
fi
echo -e "${GREEN}✓ All required environment variables present${NC}"
echo ""

# Pull latest code
echo -e "${YELLOW}Pulling latest code from git...${NC}"
git pull origin $(git branch --show-current) || {
    echo -e "${RED}Warning: Git pull failed. Continuing with current code...${NC}"
}
echo ""

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down || true
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Build Docker images
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache
echo -e "${GREEN}✓ Docker images built${NC}"
echo ""

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
echo "This will connect to your Supabase database and run pending migrations..."

# Verify the image exists
if ! docker image inspect expense-tracker-api:latest > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker image 'expense-tracker-api:latest' not found!${NC}"
    echo "This should have been built in the previous step."
    echo "Please check the build logs above for errors."
    exit 1
fi

# Create a temporary container to run migrations
echo "Running migration command..."
docker run --rm \
    -e POSTGRES_HOST="$POSTGRES_HOST" \
    -e POSTGRES_PORT="${POSTGRES_PORT:-5432}" \
    -e POSTGRES_DB="$POSTGRES_DB" \
    -e POSTGRES_USER="$POSTGRES_USER" \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    --entrypoint="" \
    expense-tracker-api:latest \
    sh -c "cd /app && alembic upgrade head"

migration_status=$?
if [ $migration_status -eq 0 ]; then
    echo -e "${GREEN}✓ Database migrations completed successfully${NC}"
else
    echo -e "${RED}Error: Database migrations failed with exit code $migration_status${NC}"
    echo ""
    echo "Common causes:"
    echo "  1. Database connection issue (check POSTGRES_* variables in .env)"
    echo "  2. Database not accessible from this server"
    echo "  3. Invalid credentials"
    echo "  4. Migration conflicts or errors"
    echo ""
    echo "To debug, try connecting manually:"
    echo "  docker run --rm -it -e POSTGRES_HOST=\"$POSTGRES_HOST\" -e POSTGRES_USER=\"$POSTGRES_USER\" -e POSTGRES_PASSWORD=\"$POSTGRES_PASSWORD\" expense-tracker-api:latest sh"
    echo ""
    echo "Or check migration logs:"
    echo "  docker run --rm -e POSTGRES_HOST=\"$POSTGRES_HOST\" -e POSTGRES_PORT=\"${POSTGRES_PORT:-5432}\" -e POSTGRES_DB=\"$POSTGRES_DB\" -e POSTGRES_USER=\"$POSTGRES_USER\" -e POSTGRES_PASSWORD=\"$POSTGRES_PASSWORD\" expense-tracker-api:latest alembic history"
    exit 1
fi
echo ""

# Start containers
echo -e "${YELLOW}Starting production containers...${NC}"
docker-compose -f docker-compose.prod.yml up -d
echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check container status
echo -e "${YELLOW}Container status:${NC}"
docker-compose -f docker-compose.prod.yml ps
echo ""

# Check health of API
echo -e "${YELLOW}Checking API health...${NC}"
max_attempts=30
attempt=0
api_healthy=false

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:${API_PORT:-8000}/health > /dev/null 2>&1; then
        api_healthy=true
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done

if [ "$api_healthy" = true ]; then
    echo -e "${GREEN}✓ API is healthy and responding${NC}"
else
    echo -e "${RED}Warning: API health check failed after 60 seconds${NC}"
    echo "Check logs with: docker-compose -f docker-compose.prod.yml logs api"
fi
echo ""

# Display running services
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Services running:"
echo "  - API: http://localhost:${API_PORT:-8000}"
echo "  - Web: http://localhost:${WEB_PORT:-3000}"
echo "  - Telegram Bot: Running"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - Check status: docker-compose -f docker-compose.prod.yml ps"
echo "  - Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  - Restart services: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo -e "${YELLOW}Note: Make sure to configure nginx/caddy as reverse proxy for your domain${NC}"
echo ""
