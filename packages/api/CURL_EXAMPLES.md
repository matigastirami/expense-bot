# Complete cURL Examples for All API Endpoints

## Table of Contents
- [Authentication](#authentication)
- [Accounts](#accounts)
- [Transactions](#transactions)
- [Analytics](#analytics)
- [Categories & Merchants](#categories--merchants-stubs)
- [Complete Workflow Example](#complete-workflow-example)

---

## Authentication

### Health Check
```bash
curl -X GET http://localhost:5000/health
```

**Response:**
```json
{
  "healthy": true,
  "timestamp": "2024-01-15T12:00:00"
}
```

---

### Sign Up (Create New User)
```bash
curl -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePassword123",
    "language_code": "en"
  }'
```

**Response:**
```json
{
  "message": "User created successfully",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "john.doe@example.com"
  }
}
```

**Error Example (Weak Password):**
```bash
curl -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "weak"
  }'
```

Response:
```json
{
  "error": "Password must be at least 8 characters long"
}
```

---

### Sign In (Login)
```bash
curl -X POST http://localhost:5000/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePassword123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "john.doe@example.com"
  }
}
```

**Error Example (Wrong Password):**
```bash
curl -X POST http://localhost:5000/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "wrongpassword"
  }'
```

Response:
```json
{
  "error": "Invalid email or password"
}
```

---

## Accounts

**Note:** Replace `YOUR_TOKEN` with the actual JWT token from signin/signup responses.

### Create Account (Bank)
```bash
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Main Checking",
    "type": "bank",
    "track_balance": true
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "Main Checking",
  "type": "bank",
  "track_balance": true,
  "created_at": "2024-01-15T12:00:00"
}
```

---

### Create Account (Wallet)
```bash
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Crypto Wallet",
    "type": "wallet",
    "track_balance": true
  }'
```

---

### Create Account (Cash)
```bash
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Wallet Cash",
    "type": "cash",
    "track_balance": false
  }'
```

---

### Create Account (Savings)
```bash
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Savings Account",
    "type": "bank"
  }'
```

**Note:** `track_balance` is optional. If not provided, it uses user's default setting.

---

### List All Accounts (With Balances)
```bash
curl -X GET "http://localhost:5000/accounts?include_balances=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
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
      "created_at": "2024-01-15T12:00:00",
      "balances": [
        {
          "currency": "USD",
          "balance": 1500.50,
          "updated_at": "2024-01-15T14:30:00"
        },
        {
          "currency": "EUR",
          "balance": 250.00,
          "updated_at": "2024-01-15T14:30:00"
        }
      ]
    },
    {
      "id": 2,
      "name": "Crypto Wallet",
      "type": "wallet",
      "track_balance": true,
      "created_at": "2024-01-15T12:05:00",
      "balances": [
        {
          "currency": "BTC",
          "balance": 0.05,
          "updated_at": "2024-01-15T14:30:00"
        }
      ]
    }
  ],
  "count": 2
}
```

---

### List All Accounts (Without Balances)
```bash
curl -X GET "http://localhost:5000/accounts?include_balances=false" \
  -H "Authorization: Bearer YOUR_TOKEN"
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
      "created_at": "2024-01-15T12:00:00"
    },
    {
      "id": 2,
      "name": "Crypto Wallet",
      "type": "wallet",
      "track_balance": true,
      "created_at": "2024-01-15T12:05:00"
    }
  ],
  "count": 2
}
```

---

### Get All Balances
```bash
curl -X GET http://localhost:5000/accounts/balances \
  -H "Authorization: Bearer YOUR_TOKEN"
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
    },
    {
      "account_id": 1,
      "account_name": "Main Checking",
      "account_type": "bank",
      "currency": "EUR",
      "balance": 250.00,
      "is_tracked": true
    },
    {
      "account_id": 2,
      "account_name": "Crypto Wallet",
      "account_type": "wallet",
      "currency": "BTC",
      "balance": 0.05,
      "is_tracked": true
    }
  ],
  "count": 3
}
```

---

### Get Balances for Specific Account
```bash
curl -X GET "http://localhost:5000/accounts/balances?account_name=Main%20Checking" \
  -H "Authorization: Bearer YOUR_TOKEN"
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
    },
    {
      "account_id": 1,
      "account_name": "Main Checking",
      "account_type": "bank",
      "currency": "EUR",
      "balance": 250.00,
      "is_tracked": true
    }
  ],
  "count": 2
}
```

---

## Transactions

### Create Income Transaction
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "income",
    "amount": 2500.00,
    "currency": "USD",
    "account_to": "Main Checking",
    "description": "Monthly Salary - January 2024",
    "date": "2024-01-15T00:00:00"
  }'
```

**Response:**
```json
{
  "id": 1,
  "type": "income",
  "amount": 2500.0,
  "currency": "USD",
  "account_from": null,
  "account_to": "Main Checking",
  "currency_to": null,
  "amount_to": null,
  "exchange_rate": null,
  "description": "Monthly Salary - January 2024",
  "date": "2024-01-15T00:00:00",
  "created_at": "2024-01-15T12:30:00"
}
```

---

### Create Income (Without Date - Uses Current Time)
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "income",
    "amount": 150.00,
    "currency": "USD",
    "account_to": "Main Checking",
    "description": "Freelance payment"
  }'
```

---

### Create Expense Transaction
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "expense",
    "amount": 85.50,
    "currency": "USD",
    "account_from": "Main Checking",
    "description": "Grocery shopping at Whole Foods",
    "date": "2024-01-16T14:30:00"
  }'
```

**Response:**
```json
{
  "id": 2,
  "type": "expense",
  "amount": 85.5,
  "currency": "USD",
  "account_from": "Main Checking",
  "account_to": null,
  "currency_to": null,
  "amount_to": null,
  "exchange_rate": null,
  "description": "Grocery shopping at Whole Foods",
  "date": "2024-01-16T14:30:00",
  "created_at": "2024-01-16T14:30:00"
}
```

---

### Create Multiple Expenses (Different Categories)
```bash
# Rent
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "expense",
    "amount": 1200.00,
    "currency": "USD",
    "account_from": "Main Checking",
    "description": "Rent - January 2024"
  }'

# Utilities
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "expense",
    "amount": 150.00,
    "currency": "USD",
    "account_from": "Main Checking",
    "description": "Electric + Water bill"
  }'

# Entertainment
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "expense",
    "amount": 45.00,
    "currency": "USD",
    "account_from": "Main Checking",
    "description": "Netflix + Spotify subscriptions"
  }'
```

---

### Create Transfer Transaction (Same Currency)
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "transfer",
    "amount": 500.00,
    "currency": "USD",
    "account_from": "Main Checking",
    "account_to": "Savings Account",
    "description": "Monthly savings transfer"
  }'
```

**Response:**
```json
{
  "id": 3,
  "type": "transfer",
  "amount": 500.0,
  "currency": "USD",
  "account_from": "Main Checking",
  "account_to": "Savings Account",
  "currency_to": null,
  "amount_to": null,
  "exchange_rate": null,
  "description": "Monthly savings transfer",
  "date": "2024-01-16T15:00:00",
  "created_at": "2024-01-16T15:00:00"
}
```

---

### Create Transfer with Fee (Different Amounts)
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "transfer",
    "amount": 100.00,
    "currency": "USD",
    "account_from": "Main Checking",
    "account_to": "Crypto Wallet",
    "amount_to": 95.00,
    "description": "Transfer with $5 fee"
  }'
```

---

### Create Transfer (Different Currencies)
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "transfer",
    "amount": 1000.00,
    "currency": "USD",
    "account_from": "Main Checking",
    "account_to": "Euro Account",
    "currency_to": "EUR",
    "amount_to": 920.00,
    "exchange_rate": 0.92,
    "description": "USD to EUR transfer"
  }'
```

---

### Create Conversion Transaction
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "conversion",
    "amount": 100.00,
    "currency": "USD",
    "currency_to": "BTC",
    "amount_to": 0.0025,
    "account_from": "Main Checking",
    "account_to": "Crypto Wallet",
    "exchange_rate": 0.000025,
    "description": "Buy Bitcoin"
  }'
```

**Response:**
```json
{
  "id": 4,
  "type": "conversion",
  "amount": 100.0,
  "currency": "USD",
  "account_from": "Main Checking",
  "account_to": "Crypto Wallet",
  "currency_to": "BTC",
  "amount_to": 0.0025,
  "exchange_rate": 0.000025,
  "description": "Buy Bitcoin",
  "date": "2024-01-16T16:00:00",
  "created_at": "2024-01-16T16:00:00"
}
```

---

### Create Conversion (Same Account)
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "transaction_type": "conversion",
    "amount": 500.00,
    "currency": "USD",
    "currency_to": "EUR",
    "amount_to": 460.00,
    "account_from": "Main Checking",
    "description": "Currency exchange in same account"
  }'
```

---

### List All Transactions (Date Range)
```bash
curl -X GET "http://localhost:5000/transactions?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "transactions": [
    {
      "id": 4,
      "type": "conversion",
      "amount": 100.0,
      "currency": "USD",
      "account_from": "Main Checking",
      "account_to": "Crypto Wallet",
      "currency_to": "BTC",
      "amount_to": 0.0025,
      "exchange_rate": 0.000025,
      "description": "Buy Bitcoin",
      "date": "2024-01-16T16:00:00",
      "created_at": "2024-01-16T16:00:00"
    },
    {
      "id": 3,
      "type": "transfer",
      "amount": 500.0,
      "currency": "USD",
      "account_from": "Main Checking",
      "account_to": "Savings Account",
      "currency_to": null,
      "amount_to": null,
      "exchange_rate": null,
      "description": "Monthly savings transfer",
      "date": "2024-01-16T15:00:00",
      "created_at": "2024-01-16T15:00:00"
    }
  ],
  "count": 2
}
```

---

### List Transactions with Pagination
```bash
# First page (10 results)
curl -X GET "http://localhost:5000/transactions?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Second page (next 10 results)
curl -X GET "http://localhost:5000/transactions?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&limit=10&offset=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get 50 results
curl -X GET "http://localhost:5000/transactions?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&limit=50&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Filter Transactions by Account
```bash
curl -X GET "http://localhost:5000/transactions?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&account_name=Main%20Checking" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Filter Transactions by Type (Income Only)
```bash
curl -X GET "http://localhost:5000/transactions?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&transaction_type=income" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Filter Transactions by Type (Expenses Only)
```bash
curl -X GET "http://localhost:5000/transactions?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&transaction_type=expense" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Filter by Account AND Type
```bash
curl -X GET "http://localhost:5000/transactions?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&account_name=Main%20Checking&transaction_type=expense" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Update Transaction Amount
```bash
curl -X PUT http://localhost:5000/transactions/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "amount": 2600.00
  }'
```

**Response:**
```json
{
  "id": 1,
  "type": "income",
  "amount": 2600.0,
  "currency": "USD",
  "description": "Monthly Salary - January 2024",
  "date": "2024-01-15T00:00:00",
  "updated_at": "2024-01-16T17:00:00"
}
```

---

### Update Transaction Description
```bash
curl -X PUT http://localhost:5000/transactions/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "description": "Grocery shopping at Whole Foods - Weekly groceries"
  }'
```

---

### Update Transaction Date
```bash
curl -X PUT http://localhost:5000/transactions/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "date": "2024-01-16T15:00:00"
  }'
```

---

### Update Multiple Fields
```bash
curl -X PUT http://localhost:5000/transactions/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "amount": 92.75,
    "description": "Grocery shopping - Updated amount",
    "date": "2024-01-16T15:30:00"
  }'
```

---

## Analytics

### Get Analytics for Current Month
```bash
curl -X GET "http://localhost:5000/analytics?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "period": {
    "from": "2024-01-01T00:00:00",
    "to": "2024-01-31T23:59:59"
  },
  "total_income": 2650.0,
  "total_expenses": 1480.5,
  "net_savings": 1169.5,
  "largest_expense": {
    "amount": 1200.0,
    "currency": "USD",
    "description": "Rent - January 2024",
    "date": "2024-01-01T00:00:00"
  },
  "largest_income": {
    "amount": 2500.0,
    "currency": "USD",
    "description": "Monthly Salary - January 2024",
    "date": "2024-01-15T00:00:00"
  }
}
```

---

### Get Analytics for Specific Currency
```bash
curl -X GET "http://localhost:5000/analytics?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&currency=USD" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Analytics for Last Week
```bash
# Example: Jan 10-16, 2024
curl -X GET "http://localhost:5000/analytics?date_from=2024-01-10T00:00:00&date_to=2024-01-16T23:59:59" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Analytics for Last 3 Months
```bash
curl -X GET "http://localhost:5000/analytics?date_from=2023-11-01T00:00:00&date_to=2024-01-31T23:59:59" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Analytics for Year
```bash
curl -X GET "http://localhost:5000/analytics?date_from=2024-01-01T00:00:00&date_to=2024-12-31T23:59:59" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Categories & Merchants (Stubs)

### List Categories
```bash
curl -X GET http://localhost:5000/categories \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "categories": [],
  "message": "Category management not yet implemented"
}
```

---

### Create Category
```bash
curl -X POST http://localhost:5000/categories \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Groceries",
    "type": "expense"
  }'
```

**Response:**
```json
{
  "error": "Category management not yet implemented"
}
```

---

### List Merchants
```bash
curl -X GET http://localhost:5000/merchants \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "merchants": [],
  "message": "Merchant management not yet implemented"
}
```

---

### Create Merchant
```bash
curl -X POST http://localhost:5000/merchants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Whole Foods"
  }'
```

**Response:**
```json
{
  "error": "Merchant management not yet implemented"
}
```

---

## Complete Workflow Example

### Step 1: Create User and Login
```bash
# Sign up
TOKEN=$(curl -s -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "workflow@example.com",
    "password": "WorkflowTest123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

---

### Step 2: Create Accounts
```bash
# Create checking account
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Checking",
    "type": "bank",
    "track_balance": true
  }'

# Create savings account
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Savings",
    "type": "bank",
    "track_balance": true
  }'

# Create cash wallet
curl -X POST http://localhost:5000/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Cash",
    "type": "cash",
    "track_balance": false
  }'
```

---

### Step 3: Add Income
```bash
# Salary
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "income",
    "amount": 3000.00,
    "currency": "USD",
    "account_to": "Checking",
    "description": "January Salary"
  }'

# Freelance work
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "income",
    "amount": 500.00,
    "currency": "USD",
    "account_to": "Checking",
    "description": "Freelance project"
  }'
```

---

### Step 4: Add Expenses
```bash
# Rent
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "expense",
    "amount": 1200.00,
    "currency": "USD",
    "account_from": "Checking",
    "description": "Rent"
  }'

# Groceries
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "expense",
    "amount": 350.00,
    "currency": "USD",
    "account_from": "Checking",
    "description": "Groceries"
  }'

# Utilities
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "expense",
    "amount": 200.00,
    "currency": "USD",
    "account_from": "Checking",
    "description": "Utilities"
  }'
```

---

### Step 5: Transfer to Savings
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "transfer",
    "amount": 500.00,
    "currency": "USD",
    "account_from": "Checking",
    "account_to": "Savings",
    "description": "Monthly savings"
  }'
```

---

### Step 6: Check Balances
```bash
curl -X GET http://localhost:5000/accounts/balances \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "balances": [
    {
      "account_id": 1,
      "account_name": "Checking",
      "account_type": "bank",
      "currency": "USD",
      "balance": 1250.0,
      "is_tracked": true
    },
    {
      "account_id": 2,
      "account_name": "Savings",
      "account_type": "bank",
      "currency": "USD",
      "balance": 500.0,
      "is_tracked": true
    }
  ],
  "count": 2
}
```

---

### Step 7: View Transactions
```bash
# Get all transactions for current month
curl -X GET "http://localhost:5000/transactions?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Step 8: Get Analytics
```bash
curl -X GET "http://localhost:5000/analytics?date_from=2024-01-01T00:00:00&date_to=2024-01-31T23:59:59" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
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
    "description": "Rent",
    "date": "2024-01-XX..."
  },
  "largest_income": {
    "amount": 3000.0,
    "currency": "USD",
    "description": "January Salary",
    "date": "2024-01-XX..."
  }
}
```

---

## Error Examples

### Missing Required Field
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "income",
    "amount": 100.00
  }'
```

**Response:**
```json
{
  "error": "Income transactions require a destination account (account_to)"
}
```

---

### Invalid Transaction Type
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "invalid",
    "amount": 100.00,
    "currency": "USD"
  }'
```

**Response:**
```json
{
  "error": "Invalid transaction type. Must be one of: income, expense, transfer, conversion"
}
```

---

### Invalid Amount
```bash
curl -X POST http://localhost:5000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "expense",
    "amount": -50.00,
    "currency": "USD",
    "account_from": "Checking"
  }'
```

**Response:**
```json
{
  "error": "Amount must be greater than 0"
}
```

---

### Unauthorized Request
```bash
curl -X GET http://localhost:5000/accounts
```

**Response:**
```json
{
  "msg": "Missing Authorization Header"
}
```

---

### Invalid Date Format
```bash
curl -X GET "http://localhost:5000/transactions?date_from=2024-01-01&date_to=2024-01-31" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "error": "Invalid date format. Use ISO format (e.g., 2024-01-01T12:00:00)"
}
```

---

## Tips

### 1. Save Token to Variable (Bash)
```bash
TOKEN=$(curl -s -X POST http://localhost:5000/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Password123"}' \
  | jq -r '.access_token')
```

### 2. Pretty Print JSON (Using jq)
```bash
curl -X GET http://localhost:5000/accounts \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### 3. Save Response to File
```bash
curl -X GET http://localhost:5000/accounts \
  -H "Authorization: Bearer $TOKEN" > accounts.json
```

### 4. Include Response Headers
```bash
curl -i -X GET http://localhost:5000/health
```

### 5. Verbose Output (Debug)
```bash
curl -v -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123"}'
```

---

## Notes

- Replace `YOUR_TOKEN` with actual JWT token from signin/signup
- Replace `localhost:5000` with your actual API URL if deployed
- All dates should be in ISO 8601 format: `YYYY-MM-DDTHH:MM:SS`
- URL encode special characters in query parameters (e.g., space = `%20`)
- Tokens expire after 1 hour by default (configurable)
