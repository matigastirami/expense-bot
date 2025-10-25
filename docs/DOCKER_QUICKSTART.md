# Docker Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Setup Environment

**Development (with local database):**
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - TELEGRAM_BOT_TOKEN
# - OPENAI_API_KEY
# - JWT_SECRET
# Database will use default local settings
```

**Production (with Supabase):**
```bash
cp .env.example .env.production
# Edit .env.production and add:
# - TELEGRAM_BOT_TOKEN
# - OPENAI_API_KEY
# - JWT_SECRET
# - Supabase connection details (POSTGRES_HOST, POSTGRES_PASSWORD, etc.)
```

### 2. Setup Database

**Development:** Database container will start automatically

**Production:** 
1. Create Supabase project at https://supabase.com
2. Get connection details from Project Settings > Database
3. Run migrations: `alembic upgrade head`

### 3. Start Services
```bash
# Development
make docker-dev-build
make docker-dev-up

# Production
make docker-prod-build
make docker-prod-up
```

### 4. Verify Everything is Running
```bash
# Check service status
docker-compose ps

# View logs
make docker-dev-logs

# Test API
curl http://localhost:8000/health
```

## 📦 Available Services

| Service | Port | Container Name | Description |
|---------|------|----------------|-------------|
| API | 8000 | expense-tracker-api | REST API |
| Telegram Bot | - | expense-tracker-bot | Telegram Interface |
| PostgreSQL (dev only) | 5433 | expense-tracker-db-dev | Local Database |

**Note:** Production uses Supabase cloud database (no PostgreSQL container)

## 🛠️ Common Commands

### Development

```bash
# Build images
make docker-dev-build

# Start all services
make docker-dev-up

# Stop all services
make docker-dev-down

# View logs (follow mode)
make docker-dev-logs

# Restart services
make docker-dev-restart

# Build specific service
make docker-build-api
make docker-build-bot
```

### Production

```bash
# Build production images
make docker-prod-build

# Start production services
make docker-prod-up

# Stop production services
make docker-prod-down

# View production logs
make docker-prod-logs

# Check service status
make docker-prod-ps
```

### Database

**Development (Local PostgreSQL):**
```bash
# Create backup
make docker-db-backup

# Restore from backup
make docker-db-restore

# Run migrations
docker-compose exec api alembic upgrade head
```

**Production (Supabase):**
```bash
# Run migrations
export $(cat .env.production | xargs)
alembic upgrade head

# Backups are automatic in Supabase
# Access via: Project Settings > Database > Backups
```

### Cleanup

```bash
# Remove all containers and volumes
make docker-clean
```

## 🔍 Troubleshooting

### Check Service Health
```bash
docker-compose ps
```

### View Service Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f bot
docker-compose logs -f postgres
```

### Rebuild After Code Changes
```bash
# Rebuild and restart
make docker-dev-build
make docker-dev-restart
```

### Database Connection Issues

**Production (Supabase):**
```bash
# Test connection from your machine
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" -c "SELECT 1;"

# Test from API container
docker-compose -f docker-compose.prod.yml exec api python -c "from libs.db.base import engine; print('OK')"

# Check Supabase project status at https://supabase.com
```

**Development (Local):**
```bash
# Check postgres health
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U finance -d finance -c "SELECT 1;"
```

### Container Won't Start
```bash
# Check logs for errors
docker-compose logs service-name

# Rebuild without cache
docker-compose build --no-cache service-name

# Full restart
docker-compose down
docker-compose up -d
```

## 🔐 Security Notes

- Never commit `.env` files
- Use strong passwords in production
- Change default JWT_SECRET (minimum 32 characters)
- **Supabase Security:**
  - Enable Row Level Security (RLS) if needed
  - Use connection pooling in production
  - Restrict API access with API keys
  - Enable 2FA on Supabase account
- Use Docker secrets for sensitive data in production

## 📊 Monitoring

### Check Resource Usage
```bash
docker stats
```

### Check Service Health
```bash
# API health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready -U finance
```

## 🎯 What's Running?

**After `make docker-dev-up` (Development):**
1. **PostgreSQL Database** - Local container ready to accept connections
2. **REST API** - Available at http://localhost:8000
3. **Telegram Bot** - Polling for messages

**After `make docker-prod-up` (Production):**
1. **REST API** - Available at http://localhost:8000 (connected to Supabase)
2. **Telegram Bot** - Polling for messages (connected to Supabase)
3. **Supabase Database** - Managed cloud database (not a container)

## 📝 Next Steps

### Development
1. ✅ Services running? Check with `docker-compose ps`
2. ✅ Database ready? Check with `docker-compose ps postgres`
3. ✅ API working? Test with `curl http://localhost:8000/health`
4. ✅ Bot responding? Send `/start` to your Telegram bot

### Production
1. ✅ Supabase project created? Check at https://supabase.com
2. ✅ Migrations run? Run `alembic upgrade head`
3. ✅ Services running? Check with `docker-compose -f docker-compose.prod.yml ps`
4. ✅ API working? Test with `curl http://localhost:8000/health`
5. ✅ Bot responding? Send `/start` to your Telegram bot

### Advanced
- Need to scale? See [DOCKER.md](./DOCKER.md) for advanced options
- Setting up CI/CD? Check deployment section in [DOCKER.md](./DOCKER.md)

## 🆘 Need Help?

- Full documentation: [DOCKER.md](./DOCKER.md)
- Service architecture: [README.md](./README.md)
- Report issues: GitHub Issues
