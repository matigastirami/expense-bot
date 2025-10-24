# Expense Tracker API - Complete Implementation ✅

A production-ready REST API for personal finance management with multi-currency support, automatic currency conversion, and comprehensive transaction tracking.

## 🚀 Quick Start

```bash
# Start the API
make dev-api

# Test it works
curl http://localhost:5000/health
```

**That's it!** The API is now running at `http://localhost:5000`

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[HOW_TO_RUN.md](packages/api/HOW_TO_RUN.md)** | All ways to start the API |
| **[CURL_EXAMPLES.md](packages/api/CURL_EXAMPLES.md)** | Complete cURL examples for every endpoint ⭐ |
| **[README.md](packages/api/README.md)** | Full API reference |
| **[START_API.md](packages/api/START_API.md)** | Startup guide and troubleshooting |
| **[QUICKSTART.md](QUICKSTART.md)** | Quick start for entire project |

## ✨ Features

- ✅ **Multi-Currency Support** - USD, EUR, ARS, BTC, and more
- ✅ **Automatic Conversion** - Real-time exchange rates with caching
- ✅ **4 Transaction Types** - Income, Expense, Transfer, Conversion
- ✅ **Balance Tracking** - Strict or Logging mode per account
- ✅ **JWT Authentication** - Secure token-based auth
- ✅ **Analytics** - Income, expenses, net savings
- ✅ **Comprehensive Validation** - All inputs validated
- ✅ **Clean Architecture** - Shared services for API and bot

## 🎯 API Endpoints

### Authentication
- `POST /signup` - Create new user
- `POST /signin` - Login and get JWT token
- `GET /health` - Health check

### Accounts
- `GET /accounts` - List all accounts
- `POST /accounts` - Create account
- `GET /accounts/balances` - Get balances

### Transactions
- `GET /transactions` - List transactions (with filters)
- `POST /transactions` - Create transaction
- `PUT /transactions/<id>` - Update transaction

### Analytics
- `GET /analytics` - Financial analytics

## 💻 Example Usage

### 1. Create User
```bash
curl -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

### 2. Create Account
```bash
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Main Checking",
    "type": "bank"
  }'
```

### 3. Add Income
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "income",
    "amount": 2500,
    "currency": "USD",
    "account_to": "Main Checking",
    "description": "Salary"
  }'
```

### 4. Add Expense
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "expense",
    "amount": 50,
    "currency": "USD",
    "account_from": "Main Checking",
    "description": "Groceries"
  }'
```

### 5. Get Analytics
```bash
curl -X GET "http://localhost:5000/analytics?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**See [CURL_EXAMPLES.md](packages/api/CURL_EXAMPLES.md) for 50+ complete examples!**

## 🏗️ Architecture

```
libs/
├── services/          # Shared business logic
│   ├── user_service.py
│   ├── account_service.py
│   └── transaction_service.py
├── validators/        # Input validation
│   ├── user_validators.py
│   ├── account_validators.py
│   └── transaction_validators.py
├── db/               # Data layer
│   ├── models.py
│   ├── crud.py
│   └── base.py
└── integrations/     # External services
    └── fx/           # Exchange rates

packages/api/         # REST API
└── src/app.py       # Flask application
```

**Key Benefit**: Services are shared between the API and Telegram bot!

## 🧪 Testing

```bash
# Run automated tests
make test-api-endpoints

# Or manually
cd packages/api
python test_api.py
```

## 🛠️ Make Commands

```bash
make dev-api              # Start the API
make test-api-endpoints   # Run API tests
make migrate              # Run database migrations
make migration-create     # Create new migration
```

## 📦 Requirements

- Python 3.11+
- PostgreSQL
- Environment variables:
  - `DATABASE_URL` - PostgreSQL connection
  - `JWT_SECRET_KEY` - JWT secret (change in production!)

## 🔐 Security

- ✅ **bcrypt** password hashing (12 rounds)
- ✅ **JWT** token authentication
- ✅ **Email validation**
- ✅ **Password strength** requirements (8+ chars, 1 letter, 1 number)
- ✅ **Input validation** on all endpoints

## 💡 Key Features Explained

### Multi-Currency Support
Automatically converts between currencies using real-time exchange rates:
- Supports 20+ currencies (USD, EUR, GBP, ARS, etc.)
- Crypto support (BTC, ETH, USDT)
- 5-minute in-memory cache
- 1-hour database cache
- Graceful fallback with pending transactions

### Transaction Types

1. **Income** - Money coming in (salary, freelance, etc.)
2. **Expense** - Money going out (rent, groceries, etc.)
3. **Transfer** - Moving money between accounts
4. **Conversion** - Exchanging currencies

Each type has specific validation rules and balance update logic.

### Balance Tracking

- **Strict Mode**: All transactions affect balances
- **Logging Mode**: Transactions recorded but don't affect balances

Can be set per-account or inherited from user settings.

## 🚀 Deployment

For production, use a WSGI server:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 'packages.api.src.app:app'
```

Don't forget to:
- ✅ Set `JWT_SECRET_KEY` to a secure random value
- ✅ Use production database
- ✅ Enable HTTPS
- ✅ Set up proper logging
- ✅ Configure CORS if needed

## 📊 API Response Examples

### Success Response
```json
{
  "id": 1,
  "type": "income",
  "amount": 2500.0,
  "currency": "USD",
  "account_to": "Main Checking",
  "description": "Salary",
  "date": "2024-01-15T00:00:00"
}
```

### Error Response
```json
{
  "error": "Invalid email or password"
}
```

### Analytics Response
```json
{
  "period": {
    "from": "2024-01-01T00:00:00",
    "to": "2024-01-31T23:59:59"
  },
  "total_income": 3500.0,
  "total_expenses": 1750.0,
  "net_savings": 1750.0,
  "largest_expense": {
    "amount": 1200.0,
    "currency": "USD",
    "description": "Rent"
  }
}
```

## 🤝 Contributing

The codebase follows clean architecture principles:

1. **Add validation** in `libs/validators/`
2. **Add business logic** in `libs/services/`
3. **Add endpoints** in `packages/api/src/app.py`
4. **Add tests** in `packages/api/test_api.py`
5. **Update docs** in `packages/api/CURL_EXAMPLES.md`

## 📝 License

[Add your license here]

## 🎉 Ready to Go!

The API is **complete and production-ready**. Start it with:

```bash
make dev-api
```

Then explore the examples:
```bash
cat packages/api/CURL_EXAMPLES.md
```

Happy coding! 🚀
