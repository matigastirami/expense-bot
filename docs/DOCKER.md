# Docker Deployment Guide

This guide explains how to deploy the Expense Tracker application using Docker.

## Architecture

The application consists of multiple services:
- **Database**: Supabase (PostgreSQL) cloud database for storing all financial data
- **API**: REST API service for programmatic access
- **Bot**: Telegram bot for user interaction
- **Agent**: (Optional) Standalone finance agent

**Note**: Production uses Supabase cloud database. Development environment includes a local PostgreSQL container for convenience.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- `.env` file with required environment variables

## Quick Start

### Development Environment

1. **Create environment file:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

2. **Start all services:**
```bash
docker-compose up -d
```

3. **View logs:**
```bash
docker-compose logs -f
```

4. **Stop services:**
```bash
docker-compose down
```

### Production Environment

1. **Setup Supabase Database:**
   - Create a Supabase project at https://supabase.com
   - Get connection details from Project Settings > Database
   - Run migrations: `alembic upgrade head`

2. **Create environment file:**
```bash
cp .env.example .env.production
# Edit .env.production with:
# - Supabase connection details
# - Your API keys (Telegram, OpenAI)
# - Production JWT secret
```

3. **Start production services:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

4. **Check service health:**
```bash
docker-compose -f docker-compose.prod.yml ps
```

## Service Details

### Database

**Production**: Supabase (PostgreSQL) Cloud
- Managed by Supabase
- Automatic backups
- Connection pooling
- Point-in-time recovery

**Development**: Local PostgreSQL Container
- **Container**: `expense-tracker-db-dev`
- **Port**: `5433:5432`
- **Health Check**: `pg_isready` command every 10s
- **Data Persistence**: Volume `postgres_data_dev`

### REST API

**Container**: `expense-tracker-api` (prod) / `expense-tracker-api-dev` (dev)

**Port**: `8000:8000`

**Dockerfile**: `packages/api/Dockerfile`

**Database**: Connects to Supabase in production, local PostgreSQL in development

**Health Check**: HTTP GET to `/health` endpoint

**Key Features**:
- JWT authentication
- User management
- Account & transaction CRUD
- Financial analytics

**Endpoints**:
- `POST /signup` - User registration
- `POST /signin` - User login
- `GET /accounts` - List accounts
- `POST /accounts` - Create account
- `GET /transactions` - List transactions
- `POST /transactions` - Create transaction
- `GET /analytics` - Financial analytics

### Telegram Bot

**Container**: `expense-tracker-bot` (prod) / `expense-tracker-bot-dev` (dev)

**Dockerfile**: `packages/telegram/Dockerfile`

**Health Check**: Bot import verification

**Key Features**:
- Natural language transaction processing
- Voice message support (requires ffmpeg)
- Bilingual support (English/Spanish)
- Interactive transaction confirmation
- Balance queries and reports

**Dependencies**:
- Requires `TELEGRAM_BOT_TOKEN`
- Uses `packages/agent` for AI processing

### Finance Agent (Optional)

**Container**: `expense-tracker-agent`

**Dockerfile**: `packages/agent/Dockerfile`

**Usage**: Standalone agent in REPL mode

**To enable**:
Uncomment the `agent` service in `docker-compose.prod.yml`

## Environment Variables

See `.env.example` for all available configuration options.

**Required Variables**:
```env
TELEGRAM_BOT_TOKEN=your-bot-token
OPENAI_API_KEY=your-openai-key
JWT_SECRET=your-jwt-secret
```

**Database Variables** (Production - Supabase):
```env
POSTGRES_HOST=db.your-project-ref.supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-supabase-password
```

**Database Variables** (Development - Local):
```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=finance
POSTGRES_USER=finance
POSTGRES_PASSWORD=finance
```

**Optional Variables**:
```env
FX_PRIMARY=coingecko
ARS_SOURCE=blue
API_PORT=8000
```

## Building Images

### Build all images:
```bash
docker-compose -f docker-compose.prod.yml build
```

### Build specific service:
```bash
docker-compose -f docker-compose.prod.yml build api
docker-compose -f docker-compose.prod.yml build bot
docker-compose -f docker-compose.prod.yml build agent
```

### Build without cache:
```bash
docker-compose -f docker-compose.prod.yml build --no-cache
```

## Managing Services

### Start specific service:
```bash
docker-compose up -d api
docker-compose up -d bot
```

### Restart service:
```bash
docker-compose restart api
docker-compose restart bot
```

### View service logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f bot

# Last 100 lines
docker-compose logs --tail=100 api
```

### Execute commands in container:
```bash
# API container
docker-compose exec api python -c "from libs.db.base import engine; print('DB connected')"

# Bot container
docker-compose exec bot python -c "from packages.telegram.bot import dp; print('Bot OK')"

# Interactive shell
docker-compose exec api bash
```

## Database Management

### Production (Supabase)

**Run migrations:**
```bash
# Set Supabase connection in .env
export $(cat .env | xargs)
alembic upgrade head
```

**Create migration:**
```bash
alembic revision --autogenerate -m "migration description"
```

**Backups:**
Supabase provides automatic daily backups. Access them from:
- Project Settings > Database > Backups
- Download point-in-time backups
- Restore from Supabase dashboard

**Manual backup (if needed):**
```bash
pg_dump "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" > backup.sql
```

### Development (Local PostgreSQL)

**Run migrations:**
```bash
docker-compose exec api alembic upgrade head
```

**Create migration:**
```bash
docker-compose exec api alembic revision --autogenerate -m "migration description"
```

**Database backup:**
```bash
make docker-db-backup
# or
docker-compose exec postgres pg_dump -U finance finance > backup.sql
```

**Database restore:**
```bash
make docker-db-restore
# or
docker-compose exec -T postgres psql -U finance finance < backup.sql
```

## Networking

All services communicate through the `expense-tracker-network` (prod) or `expense-tracker-dev` (dev) bridge network.

**Service DNS names** (Development):
- `postgres` - Local PostgreSQL database
- `api` - REST API
- `bot` - Telegram Bot

**Production**:
- Services connect to Supabase cloud database via internet
- API and Bot communicate through shared network

## Volumes

**Production**:
- No volumes needed (Supabase handles database persistence)

**Development**:
- `postgres_data_dev` - Local database persistence
- Source code mounted for hot reload

## Health Checks

All services include health checks:

**Check service health**:
```bash
docker-compose ps
```

**Healthy indicators**:
- `postgres`: "healthy" status
- `api`: Returns 200 from `/health`
- `bot`: Can import bot module

## Troubleshooting

### Service won't start:
```bash
# Check logs
docker-compose logs service-name

# Rebuild image
docker-compose build --no-cache service-name

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Database connection issues:

**Production (Supabase):**
```bash
# Test connection
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" -c "SELECT 1;"

# Check from container
docker-compose exec api python -c "from libs.db.base import engine; import asyncio; asyncio.run(engine.connect())"
```

**Development (Local):**
```bash
# Check postgres is healthy
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U finance -d finance -c "SELECT 1;"
```

### Port conflicts:
```bash
# Check what's using the port
lsof -i :8000
lsof -i :5432

# Change port in docker-compose.yml or .env
```

### Permission issues:
```bash
# Fix volume permissions
sudo chown -R $(id -u):$(id -g) postgres_data/
```

## Production Best Practices

1. **Use secrets management**: Don't commit `.env` files
2. **Set resource limits**: Add memory/CPU limits to services
3. **Enable logging driver**: Configure proper log aggregation
4. **Use docker secrets**: For sensitive data in swarm mode
5. **Regular backups**: Automate database backups
6. **Monitor health**: Set up alerting for unhealthy services
7. **Update images**: Keep base images and dependencies updated
8. **Network security**: Use internal networks, expose only necessary ports

## Scaling (Docker Swarm/Kubernetes)

The API service can be scaled horizontally:

```bash
# Docker Swarm
docker service scale expense-tracker_api=3

# Docker Compose (limited)
docker-compose up -d --scale api=3
```

**Note**: Bot should NOT be scaled (Telegram bot polling limitation)

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
- name: Build and push Docker images
  run: |
    docker-compose -f docker-compose.prod.yml build
    docker-compose -f docker-compose.prod.yml push
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)

## Support

For issues, check:
1. Service logs: `docker-compose logs`
2. Container status: `docker-compose ps`
3. Network connectivity: `docker network inspect expense-tracker-network`
4. GitHub Issues: [Repository Issues](https://github.com/yourrepo/issues)
