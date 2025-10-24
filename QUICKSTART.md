# Expense Tracker - Quick Start Guide

## Project Overview

This is a personal finance management system with:
- **REST API** (Flask) for web/mobile clients
- **Telegram Bot** for conversational expense tracking
- **Shared Services** for consistent business logic across both interfaces

## Project Structure

```
expense-tracker-claude/
├── libs/                          # Shared libraries
│   ├── db/                        # Database models, CRUD, migrations
│   ├── services/                  # Business logic services (NEW!)
│   │   ├── user_service.py
│   │   ├── account_service.py
│   │   ├── transaction_service.py
│   │   └── audio_transcription.py
│   ├── validators/                # Input validation (NEW!)
│   │   ├── user_validators.py
│   │   ├── account_validators.py
│   │   └── transaction_validators.py
│   ├── integrations/              # External services (FX rates, etc.)
│   └── reports/                   # PDF report generation
├── packages/
│   ├── api/                       # REST API (Flask)
│   │   └── src/app.py            # Main API (REFACTORED)
│   └── agent/                     # Telegram bot
│       └── agent.py               # Bot logic
└── README.md
```

## Prerequisites

- Python 3.11+
- PostgreSQL database
- (Optional) Telegram bot token for bot functionality

## Environment Setup

### 1. Install Dependencies

```bash
# From project root
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/expense_tracker

# JWT for API authentication
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production

# FX Service (for currency conversion)
ARS_SOURCE=dolarapi  # or another ARS provider

# Telegram Bot (optional, for bot functionality)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# OpenAI (for voice transcription and AI features)
OPENAI_API_KEY=your-openai-api-key
```

### 3. Database Setup

```bash
# Create database
createdb expense_tracker

# Run migrations
cd libs/db
alembic upgrade head
```

## Running the Application

### Option 1: REST API Only

```bash
# From project root (recommended)
python packages/api/run.py

# Or use the shell script
./run_api.sh

# API will be available at http://localhost:5000
```

### Option 2: Telegram Bot Only

```bash
# From project root
cd packages/agent
python bot.py  # or your bot entry file
```

### Option 3: Both (Different Terminals)

Terminal 1:
```bash
cd packages/api
python run.py
```

Terminal 2:
```bash
cd packages/agent
python bot.py
```

## Testing the API

### Quick Test

```bash
# Health check
curl http://localhost:5000/health
```

### Comprehensive Tests

```bash
cd packages/api
python test_api.py
```

This will:
- Create a test user
- Test authentication
- Create accounts
- Create transactions
- Test analytics
- Print results summary

### Manual Testing Examples

```bash
# Sign up
curl -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Password123"}'

# Sign in
curl -X POST http://localhost:5000/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Password123"}'

# Create account (use token from signin)
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name":"My Checking","type":"bank"}'

# Create income transaction
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type":"income",
    "amount":2000,
    "currency":"USD",
    "account_to":"My Checking",
    "description":"Salary"
  }'

# List transactions
curl "http://localhost:5000/transactions?date_from=2024-01-01T00:00:00&date_to=2024-12-31T23:59:59" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Common Tasks

### Create a Migration

```bash
cd libs/db
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

### Reset Database

```bash
dropdb expense_tracker
createdb expense_tracker
cd libs/db
alembic upgrade head
```

### Add a New API Endpoint

1. Add route to `packages/api/src/app.py`
2. Use services from `libs/services/`
3. Use validators from `libs/validators/`
4. Update `packages/api/README.md`
5. Add test to `packages/api/test_api.py`

### Add a New Service

1. Create service file in `libs/services/`
2. Add validation in `libs/validators/`
3. Export from `libs/services/__init__.py`
4. Use in both API and agent

## Key Features

### Multi-Currency Support
- Automatic currency conversion using real-time exchange rates
- Support for fiat currencies and cryptocurrencies
- Caching for performance (5 min in-memory, 1 hour in DB)

### Transaction Types
1. **Income** - Money coming in (salary, freelance, etc.)
2. **Expense** - Money going out (groceries, rent, etc.)
3. **Transfer** - Moving money between accounts
4. **Conversion** - Exchanging currencies

### Balance Tracking Modes
- **Strict** - All transactions affect balances
- **Logging** - Transactions recorded but don't affect balances

### Authentication
- JWT-based authentication for API
- Telegram ID-based for bot
- Email/password with bcrypt hashing

## Documentation

- **API Documentation**: `packages/api/README.md`
- **Refactoring Summary**: `REFACTORING_SUMMARY.md`
- **Database Models**: `libs/db/models.py`

## Development Workflow

### 1. Make Changes
- Edit code in `libs/services/` for business logic
- Edit `packages/api/src/app.py` for API endpoints
- Edit `packages/agent/` for bot functionality

### 2. Test
```bash
# Run API tests
cd packages/api
python test_api.py

# Manual testing
# Start API and use curl or Postman
```

### 3. Database Changes
```bash
# Create migration
cd libs/db
alembic revision --autogenerate -m "description"

# Review migration file in libs/db/migrations/versions/

# Apply migration
alembic upgrade head
```

### 4. Commit
```bash
git add .
git commit -m "Description of changes"
```

## Troubleshooting

### "Connection refused" when testing API
- Make sure the API is running: `cd packages/api && python run.py`
- Check if port 5000 is already in use

### Database connection errors
- Verify DATABASE_URL in `.env`
- Ensure PostgreSQL is running
- Check if database exists: `psql -l`

### Import errors
- Make sure you're running from project root
- Check Python path includes project root
- Verify all dependencies are installed

### Migration errors
- Check database is up: `psql expense_tracker`
- Review migration files for conflicts
- Try: `alembic downgrade -1` then `alembic upgrade head`

## Production Deployment

### Environment Variables
- Set `JWT_SECRET_KEY` to a secure random value
- Use production database URL
- Set appropriate API rate limits

### Security
- Enable HTTPS
- Set up CORS appropriately
- Use environment-specific secrets
- Enable rate limiting

### Database
- Use connection pooling
- Set up regular backups
- Monitor query performance

### Monitoring
- Add application logging
- Set up error tracking (Sentry, etc.)
- Monitor API response times

## Next Steps

1. **For API Development**:
   - Implement category management
   - Implement merchant tracking
   - Add more analytics endpoints
   - Add export functionality (CSV, PDF)

2. **For Bot Development**:
   - Migrate to use shared services
   - Add more conversational features
   - Improve natural language processing

3. **For Both**:
   - Add unit tests
   - Add integration tests
   - Improve error handling
   - Add request logging

## Getting Help

- Check the API documentation: `packages/api/README.md`
- Review the refactoring summary: `REFACTORING_SUMMARY.md`
- Look at test examples: `packages/api/test_api.py`

## License

[Add your license here]
