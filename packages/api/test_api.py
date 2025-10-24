"""
Simple test script for the Expense Tracker API.

This script tests the main API endpoints to ensure they work correctly.
Run this after starting the API server.
"""

import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:5000"

# Test data
TEST_EMAIL = f"test_{datetime.now().timestamp()}@example.com"
TEST_PASSWORD = "TestPassword123"

def print_response(name, response):
    """Print formatted response."""
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test health check endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    return response.status_code == 200

def test_signup():
    """Test user signup."""
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "language_code": "en"
    }
    response = requests.post(f"{BASE_URL}/signup", json=data)
    print_response("Sign Up", response)

    if response.status_code == 201:
        return response.json().get("access_token")
    return None

def test_signin(email, password):
    """Test user signin."""
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/signin", json=data)
    print_response("Sign In", response)

    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_create_account(token):
    """Test account creation."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Test Checking",
        "type": "bank",
        "track_balance": True
    }
    response = requests.post(f"{BASE_URL}/accounts", json=data, headers=headers)
    print_response("Create Account", response)
    return response.status_code == 201

def test_list_accounts(token):
    """Test listing accounts."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/accounts?include_balances=true", headers=headers)
    print_response("List Accounts", response)
    return response.status_code == 200

def test_create_income(token):
    """Test creating income transaction."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "transaction_type": "income",
        "amount": 2000.00,
        "currency": "USD",
        "account_to": "Test Checking",
        "description": "Test Salary"
    }
    response = requests.post(f"{BASE_URL}/transactions", json=data, headers=headers)
    print_response("Create Income Transaction", response)
    return response.status_code == 201

def test_create_expense(token):
    """Test creating expense transaction."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "transaction_type": "expense",
        "amount": 50.00,
        "currency": "USD",
        "account_from": "Test Checking",
        "description": "Test Grocery Shopping"
    }
    response = requests.post(f"{BASE_URL}/transactions", json=data, headers=headers)
    print_response("Create Expense Transaction", response)
    return response.status_code == 201

def test_list_transactions(token):
    """Test listing transactions."""
    headers = {"Authorization": f"Bearer {token}"}

    # Date range: last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    params = {
        "date_from": start_date.isoformat(),
        "date_to": end_date.isoformat(),
        "limit": 10
    }

    response = requests.get(f"{BASE_URL}/transactions", params=params, headers=headers)
    print_response("List Transactions", response)
    return response.status_code == 200

def test_get_balances(token):
    """Test getting account balances."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/accounts/balances", headers=headers)
    print_response("Get Balances", response)
    return response.status_code == 200

def test_analytics(token):
    """Test analytics endpoint."""
    headers = {"Authorization": f"Bearer {token}"}

    # Date range: last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    params = {
        "date_from": start_date.isoformat(),
        "date_to": end_date.isoformat(),
        "currency": "USD"
    }

    response = requests.get(f"{BASE_URL}/analytics", params=params, headers=headers)
    print_response("Analytics", response)
    return response.status_code == 200

def run_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("EXPENSE TRACKER API TESTS")
    print("="*60)

    results = {}

    # Test health check
    print("\n[1/9] Testing health check...")
    results["health_check"] = test_health_check()

    # Test signup
    print("\n[2/9] Testing signup...")
    token = test_signup()
    results["signup"] = token is not None

    if not token:
        print("\n❌ Signup failed. Cannot continue with other tests.")
        return results

    # Test signin
    print("\n[3/9] Testing signin...")
    signin_token = test_signin(TEST_EMAIL, TEST_PASSWORD)
    results["signin"] = signin_token is not None

    # Test create account
    print("\n[4/9] Testing create account...")
    results["create_account"] = test_create_account(token)

    # Test list accounts
    print("\n[5/9] Testing list accounts...")
    results["list_accounts"] = test_list_accounts(token)

    # Test create income
    print("\n[6/9] Testing create income transaction...")
    results["create_income"] = test_create_income(token)

    # Test create expense
    print("\n[7/9] Testing create expense transaction...")
    results["create_expense"] = test_create_expense(token)

    # Test list transactions
    print("\n[8/9] Testing list transactions...")
    results["list_transactions"] = test_list_transactions(token)

    # Test get balances
    print("\n[9/9] Testing get balances...")
    results["get_balances"] = test_get_balances(token)

    # Test analytics
    print("\n[10/10] Testing analytics...")
    results["analytics"] = test_analytics(token)

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_flag in results.items():
        status = "✅ PASSED" if passed_flag else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60 + "\n")

    return results

if __name__ == "__main__":
    try:
        results = run_tests()

        # Exit with error code if any tests failed
        if not all(results.values()):
            exit(1)
        else:
            print("\n✅ All tests passed!\n")
            exit(0)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server.")
        print("Make sure the API server is running at http://localhost:5000\n")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        exit(1)
