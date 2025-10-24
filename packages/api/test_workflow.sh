#!/bin/bash

# Complete workflow test for Expense Tracker API
# This script demonstrates the full API flow

API_URL="http://localhost:5000"
EMAIL="test_$(date +%s)@example.com"
PASSWORD="TestPassword123"

echo "================================="
echo "Expense Tracker API Test Workflow"
echo "================================="
echo ""

# Step 1: Sign up
echo "Step 1: Creating new user..."
SIGNUP_RESPONSE=$(curl -s -X POST "$API_URL/signup" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

echo "$SIGNUP_RESPONSE" | jq .

# Extract token
TOKEN=$(echo "$SIGNUP_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token from signup"
    exit 1
fi

echo ""
echo "✅ Token obtained: ${TOKEN:0:50}..."
echo ""

# Step 2: Create account
echo "Step 2: Creating account..."
ACCOUNT_RESPONSE=$(curl -s -X POST "$API_URL/accounts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Main Checking",
    "type": "bank",
    "track_balance": true
  }')

echo "$ACCOUNT_RESPONSE" | jq .
echo ""

# Step 3: List accounts
echo "Step 3: Listing accounts..."
curl -s -X GET "$API_URL/accounts?include_balances=true" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# Step 4: Create income transaction
echo "Step 4: Creating income transaction..."
INCOME_RESPONSE=$(curl -s -X POST "$API_URL/transactions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "income",
    "amount": 2500,
    "currency": "USD",
    "account_to": "Main Checking",
    "description": "Monthly Salary"
  }')

echo "$INCOME_RESPONSE" | jq .
echo ""

# Step 5: Create expense transaction
echo "Step 5: Creating expense transaction..."
EXPENSE_RESPONSE=$(curl -s -X POST "$API_URL/transactions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "transaction_type": "expense",
    "amount": 85.50,
    "currency": "USD",
    "account_from": "Main Checking",
    "description": "Groceries"
  }')

echo "$EXPENSE_RESPONSE" | jq .
echo ""

# Step 6: Get balances
echo "Step 6: Getting account balances..."
curl -s -X GET "$API_URL/accounts/balances" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# Step 7: Get analytics
echo "Step 7: Getting analytics..."
DATE_FROM="2024-01-01T00:00:00"
DATE_TO="2025-12-31T23:59:59"

curl -s -X GET "$API_URL/analytics?date_from=$DATE_FROM&date_to=$DATE_TO" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

# Step 8: List transactions
echo "Step 8: Listing transactions..."
curl -s -X GET "$API_URL/transactions?date_from=$DATE_FROM&date_to=$DATE_TO&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

echo "================================="
echo "✅ Workflow completed successfully!"
echo "================================="
echo ""
echo "User: $EMAIL"
echo "Token: $TOKEN"
echo ""
echo "You can now use this token for manual testing:"
echo "export TOKEN=\"$TOKEN\""
echo ""
