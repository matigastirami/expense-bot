#!/bin/bash

# Quick script to get a valid JWT token from the API

API_URL="${API_URL:-http://localhost:5000}"

if [ $# -eq 0 ]; then
    # Create new user with timestamp
    EMAIL="test_$(date +%s)@example.com"
    PASSWORD="TestPassword123"

    echo "Creating new user: $EMAIL"

    RESPONSE=$(curl -s -X POST "$API_URL/signup" \
      -H "Content-Type: application/json" \
      -d "{
        \"email\": \"$EMAIL\",
        \"password\": \"$PASSWORD\"
      }")
else
    # Use provided credentials
    EMAIL="$1"
    PASSWORD="$2"

    echo "Signing in as: $EMAIL"

    RESPONSE=$(curl -s -X POST "$API_URL/signin" \
      -H "Content-Type: application/json" \
      -d "{
        \"email\": \"$EMAIL\",
        \"password\": \"$PASSWORD\"
      }")
fi

# Extract token
TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo ""
    echo "❌ Failed to get token"
    echo "Response:"
    echo "$RESPONSE" | jq .
    exit 1
fi

echo ""
echo "✅ Token obtained successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TOKEN=$TOKEN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Export to use in your shell:"
echo "export TOKEN=\"$TOKEN\""
echo ""
echo "Or copy this for your cURL commands:"
echo "--header 'Authorization: Bearer $TOKEN'"
echo ""
echo "User credentials:"
echo "Email: $EMAIL"
echo "Password: $PASSWORD"
echo ""
