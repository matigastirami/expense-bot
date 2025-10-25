# Expense Tracker API

A RESTful API for managing personal finances, including transactions, accounts, and analytics.

## Features

- **User Authentication**: JWT-based authentication with email/password
- **Account Management**: Create and manage multiple accounts (bank, wallet, cash, etc.)
- **Transaction Tracking**: Record income, expenses, transfers, and currency conversions
- **Multi-Currency Support**: Automatic currency conversion with real-time exchange rates
- **Balance Tracking**: Optional balance tracking per account
- **Analytics**: Financial analytics and reports

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Environment variables configured

### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost/expense_tracker
JWT_SECRET_KEY=your-secret-key-here
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
python -m packages.api.src.app
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Authentication

#### Sign Up
```http
POST /signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "language_code": "en" // optional
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com"
  }
}
```

#### Sign In
```http
POST /signin
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com"
  }
}
```

### Accounts

#### List Accounts
```http
GET /accounts?include_balances=true
Authorization: Bearer <token>
```

**Response:**
```json
{
  "accounts": [
    {
      "id": 1,
      "name": "Main Checking",
      "type": "bank",
      "track_balance": true,
      "created_at": "2024-01-01T12:00:00",
      "balances": [
        {
          "currency": "USD",
          "balance": 1500.50,
          "updated_at": "2024-01-15T10:30:00"
        }
      ]
    }
  ],
  "count": 1
}
```

#### Create Account
```http
POST /accounts
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Savings Account",
  "type": "bank",  // bank, wallet, cash, other
  "track_balance": true  // optional
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Savings Account",
  "type": "bank",
  "track_balance": true,
  "created_at": "2024-01-15T12:00:00"
}
```

#### Get Balances
```http
GET /accounts/balances?account_name=Main%20Checking
Authorization: Bearer <token>
```

**Response:**
```json
{
  "balances": [
    {
      "account_id": 1,
      "account_name": "Main Checking",
      "account_type": "bank",
      "currency": "USD",
      "balance": 1500.50,
      "is_tracked": true
    }
  ],
  "count": 1
}
```

### Transactions

#### List Transactions
```http
GET /transactions?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&limit=10&offset=0
Authorization: Bearer <token>
```

**Query Parameters:**
- `date_from` (required): Start date in ISO format
- `date_to` (required): End date in ISO format
- `account_name` (optional): Filter by account name
- `transaction_type` (optional): Filter by type (income, expense, transfer, conversion)
- `limit` (optional): Maximum results (default: 10)
- `offset` (optional): Skip results (default: 0)

**Response:**
```json
{
  "transactions": [
    {
      "id": 1,
      "type": "expense",
      "amount": 50.00,
      "currency": "USD",
      "account_from": "Main Checking",
      "account_to": null,
      "description": "Grocery shopping",
      "date": "2024-01-15T14:30:00",
      "created_at": "2024-01-15T14:30:00"
    }
  ],
  "count": 1
}
```

#### Create Transaction

**Income:**
```http
POST /transactions
Authorization: Bearer <token>
Content-Type: application/json

{
  "transaction_type": "income",
  "amount": 2000.00,
  "currency": "USD",
  "account_to": "Main Checking",
  "description": "Salary",
  "date": "2024-01-15T00:00:00"  // optional, defaults to now
}
```

**Expense:**
```http
POST /transactions
Authorization: Bearer <token>
Content-Type: application/json

{
  "transaction_type": "expense",
  "amount": 50.00,
  "currency": "USD",
  "account_from": "Main Checking",
  "description": "Grocery shopping"
}
```

**Transfer:**
```http
POST /transactions
Authorization: Bearer <token>
Content-Type: application/json

{
  "transaction_type": "transfer",
  "amount": 500.00,
  "currency": "USD",
  "account_from": "Main Checking",
  "account_to": "Savings Account",
  "description": "Monthly savings"
}
```

**Conversion:**
```http
POST /transactions
Authorization: Bearer <token>
Content-Type: application/json

{
  "transaction_type": "conversion",
  "amount": 100.00,
  "currency": "USD",
  "currency_to": "EUR",
  "amount_to": 92.50,
  "account_from": "Main Checking",
  "exchange_rate": 0.925,  // optional
  "description": "Currency exchange"
}
```

**Response:**
```json
{
  "id": 1,
  "type": "expense",
  "amount": 50.00,
  "currency": "USD",
  "account_from": "Main Checking",
  "account_to": null,
  "description": "Grocery shopping",
  "date": "2024-01-15T14:30:00",
  "created_at": "2024-01-15T14:30:00"
}
```

#### Update Transaction
```http
PUT /transactions/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 55.00,  // optional
  "description": "Grocery shopping at Whole Foods",  // optional
  "date": "2024-01-15T15:00:00"  // optional
}
```

### Analytics

#### Get Financial Analytics
```http
GET /analytics?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&currency=USD
Authorization: Bearer <token>
```

**Query Parameters:**
- `date_from` (required): Start date in ISO format
- `date_to` (required): End date in ISO format
- `currency` (optional): Currency for aggregation

**Response:**
```json
{
  "period": {
    "from": "2024-01-01T00:00:00",
    "to": "2024-01-31T23:59:59"
  },
  "total_income": 4000.00,
  "total_expenses": 2500.00,
  "net_savings": 1500.00,
  "largest_expense": {
    "amount": 500.00,
    "currency": "USD",
    "description": "Rent",
    "date": "2024-01-01T00:00:00"
  },
  "largest_income": {
    "amount": 2000.00,
    "currency": "USD",
    "description": "Salary",
    "date": "2024-01-15T00:00:00"
  }
}
```

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "healthy": true,
  "timestamp": "2024-01-15T12:00:00"
}
```

## Transaction Types

### Income
- Adds money to an account
- **Required fields**: `transaction_type`, `amount`, `currency`, `account_to`

### Expense
- Removes money from an account
- **Required fields**: `transaction_type`, `amount`, `currency`, `account_from`

### Transfer
- Moves money between accounts
- Supports different currencies with automatic conversion
- Supports fees (use `amount_to` for net amount received)
- **Required fields**: `transaction_type`, `amount`, `currency`, `account_from`, `account_to`

### Conversion
- Exchanges one currency for another within the same or different accounts
- **Required fields**: `transaction_type`, `amount`, `currency`, `currency_to`, `amount_to`, `account_from`

## Currency Conversion

The API automatically handles currency conversions:
- Uses real-time exchange rates from external providers
- Caches rates for 5 minutes (in-memory) and 1 hour (database)
- If exchange rate is unavailable, transaction is queued for retry
- Supports multiple currency providers (ARS, crypto via CoinGecko, etc.)

## Balance Tracking

Accounts can have two balance tracking modes:
- **Strict**: All transactions affect account balances
- **Logging**: Transactions are recorded but don't affect balances (for tracking only)

Set the mode per-account using the `track_balance` field, or inherit from user settings.

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "Description of what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `202`: Accepted (transaction queued)
- `400`: Bad request (validation error)
- `401`: Unauthorized (invalid credentials)
- `404`: Not found
- `500`: Internal server error
- `501`: Not implemented

## Validation Rules

### Email
- Valid email format
- Max 255 characters

### Password
- Min 8 characters
- Max 128 characters
- At least one letter
- At least one number

### Currency
- 2-10 uppercase characters
- Alphanumeric only

### Amount
- Must be positive
- Max 8 decimal places

### Account Name
- 1-255 characters
- Letters, numbers, spaces, and common punctuation

### Description
- Max 500 characters

## Future Endpoints (Not Yet Implemented)

The following endpoints are planned but not yet implemented:

- `GET /categories` - List expense categories
- `POST /categories` - Create expense category
- `GET /merchants` - List merchants/shops
- `POST /merchants` - Create merchant/shop

## Architecture

The API is built with:
- **Flask**: Web framework
- **SQLAlchemy**: ORM with async support
- **PostgreSQL**: Database
- **JWT**: Authentication
- **bcrypt**: Password hashing

Services are organized in layers:
- **API Layer**: Flask routes (`packages/api/src/app.py`)
- **Service Layer**: Business logic (`libs/services/`)
- **Data Layer**: Database operations (`libs/db/`)
- **Validation Layer**: Input validation (`libs/validators/`)

All business logic is in shared services (`libs/services`) so it can be used by both the API and the Telegram bot agent.
