"""Main Flask application for expense tracker API."""

from datetime import datetime, timedelta
import os
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from libs.db.base import async_session_maker
from libs.services.user_service import UserService
from libs.services.transaction_service import TransactionService
from libs.services.account_service import AccountService
from libs.db.crud import TransactionCRUD
from libs.db.models import TransactionType


app = Flask(__name__)

# JWT Configuration
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY", "your-secret-key-change-this"
)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Initialize JWT Manager
jwt = JWTManager(app)


# ==================== Health Check ====================

@app.route("/health", methods=["GET"])
def get_health():
    """Health check endpoint."""
    return jsonify({"healthy": True, "timestamp": datetime.now().isoformat()})


# ==================== Authentication ====================

@app.route("/signin", methods=["POST"])
async def signin():
    """
    Sign in with email and password.

    Request body:
        - email: User email
        - password: User password

    Returns:
        - access_token: JWT token for authentication
    """
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    async with async_session_maker() as session:
        user, error = await UserService.authenticate_user(
            session=session,
            email=email,
            password=password,
        )

        if error:
            return jsonify({"error": error}), 401

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"email": user.email}
        )

        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
            }
        }), 200


@app.route("/signup", methods=["POST"])
async def signup():
    """
    Create a new user account.

    Request body:
        - email: User email
        - password: User password
        - language_code: (Optional) User language preference

    Returns:
        - access_token: JWT token for authentication
        - user: User information
    """
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    language_code = data.get("language_code")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    async with async_session_maker() as session:
        user, error = await UserService.create_user(
            session=session,
            email=email,
            password=password,
            language_code=language_code,
        )

        if error:
            return jsonify({"error": error}), 400

        # Generate access token for the new user
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"email": user.email}
        )

        return jsonify({
            "message": "User created successfully",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "email": user.email,
            }
        }), 201


# ==================== Accounts ====================

@app.route("/accounts", methods=["GET"])
@jwt_required()
async def list_accounts():
    """
    List all accounts for the authenticated user.

    Query params:
        - include_balances: Include balance information (default: true)

    Returns:
        - accounts: List of accounts with optional balance information
    """
    current_user_id = int(get_jwt_identity())
    include_balances = request.args.get("include_balances", "true").lower() == "true"

    async with async_session_maker() as session:
        accounts = await AccountService.list_accounts(
            session=session,
            user_id=current_user_id,
            include_balances=include_balances,
        )

        result = []
        for account in accounts:
            account_data = {
                "id": account.id,
                "name": account.name,
                "type": account.type,
                "track_balance": account.track_balance,
                "created_at": account.created_at.isoformat(),
            }

            if include_balances and hasattr(account, 'balances'):
                account_data["balances"] = [
                    {
                        "currency": balance.currency,
                        "balance": float(balance.balance),
                        "updated_at": balance.updated_at.isoformat(),
                    }
                    for balance in account.balances
                ]

            result.append(account_data)

        return jsonify({
            "accounts": result,
            "count": len(result),
        }), 200


@app.route("/accounts", methods=["POST"])
@jwt_required()
async def create_account():
    """
    Create a new account for the authenticated user.

    Request body:
        - name: Account name (required)
        - type: Account type (bank, wallet, cash, other) (required)
        - track_balance: Whether to track balance (optional)

    Returns:
        - account: Created account information
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    name = data.get("name")
    account_type = data.get("type")
    track_balance = data.get("track_balance")

    if not name or not account_type:
        return jsonify({"error": "name and type are required"}), 400

    async with async_session_maker() as session:
        account, error = await AccountService.create_account(
            session=session,
            user_id=current_user_id,
            name=name,
            account_type=account_type,
            track_balance=track_balance,
        )

        if error:
            return jsonify({"error": error}), 400

        return jsonify({
            "id": account.id,
            "name": account.name,
            "type": account.type,
            "track_balance": account.track_balance,
            "created_at": account.created_at.isoformat(),
        }), 201


@app.route("/accounts/balances", methods=["GET"])
@jwt_required()
async def get_balances():
    """
    Get all account balances for the authenticated user.

    Query params:
        - account_name: Filter by specific account (optional)

    Returns:
        - balances: List of account balances
    """
    current_user_id = int(get_jwt_identity())
    account_name = request.args.get("account_name")

    async with async_session_maker() as session:
        balances = await AccountService.get_all_balances(
            session=session,
            user_id=current_user_id,
            account_name=account_name,
        )

        return jsonify({
            "balances": balances,
            "count": len(balances),
        }), 200


# ==================== Transactions ====================

@app.route("/transactions", methods=["GET"])
@jwt_required()
async def list_transactions():
    """
    List transactions for the authenticated user.

    Query params:
        - date_from: Start date (ISO format) (required)
        - date_to: End date (ISO format) (required)
        - account_name: Filter by account name (optional)
        - transaction_type: Filter by type (income, expense, transfer, conversion) (optional)
        - limit: Maximum number of results (default: 10)
        - offset: Number of results to skip (default: 0)

    Returns:
        - transactions: List of transactions
        - count: Number of transactions returned
    """
    current_user_id = int(get_jwt_identity())

    # Parse query parameters
    date_from_str = request.args.get("date_from")
    date_to_str = request.args.get("date_to")
    account_name = request.args.get("account_name")
    transaction_type = request.args.get("transaction_type")
    limit = int(request.args.get("limit", 10))
    offset = int(request.args.get("offset", 0))

    # Validate required parameters
    if not date_from_str or not date_to_str:
        return jsonify({"error": "date_from and date_to are required"}), 400

    # Parse dates
    try:
        date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
        date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO format (e.g., 2024-01-01T12:00:00)"}), 400

    async with async_session_maker() as session:
        transactions, error = await TransactionService.list_transactions(
            session=session,
            user_id=current_user_id,
            start_date=date_from,
            end_date=date_to,
            account_name=account_name,
            transaction_type=transaction_type,
            limit=limit,
            offset=offset,
        )

        if error:
            return jsonify({"error": error}), 400

        return jsonify({
            "transactions": transactions,
            "count": len(transactions),
        }), 200


@app.route("/transactions", methods=["POST"])
@jwt_required()
async def create_transaction():
    """
    Create a new transaction.

    Request body:
        - transaction_type: Type (income, expense, transfer, conversion) (required)
        - amount: Transaction amount (required)
        - currency: Currency code (required)
        - date: Transaction date (ISO format) (optional, defaults to now)
        - account_from: Source account name (required for expense, transfer, conversion)
        - account_to: Destination account name (required for income, transfer)
        - currency_to: Destination currency (for conversion/transfer with different currency)
        - amount_to: Destination amount (for transfer with fees or conversion)
        - exchange_rate: Exchange rate (optional)
        - description: Transaction description (optional)

    Returns:
        - transaction: Created transaction information
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    # Extract required fields
    transaction_type = data.get("transaction_type")
    amount = data.get("amount")
    currency = data.get("currency")

    # Extract optional fields
    date_str = data.get("date")
    account_from = data.get("account_from")
    account_to = data.get("account_to")
    currency_to = data.get("currency_to")
    amount_to = data.get("amount_to")
    exchange_rate = data.get("exchange_rate")
    description = data.get("description")

    # Validate required fields
    if not all([transaction_type, amount, currency]):
        return jsonify({"error": "transaction_type, amount, and currency are required"}), 400

    # Parse date if provided
    date = None
    if date_str:
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "Invalid date format. Use ISO format"}), 400

    async with async_session_maker() as session:
        transaction, error = await TransactionService.create_transaction(
            session=session,
            user_id=current_user_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            date=date,
            account_from=account_from,
            account_to=account_to,
            currency_to=currency_to,
            amount_to=amount_to,
            exchange_rate=exchange_rate,
            description=description,
        )

        if error:
            # Check if it's a queued transaction (informational message, not an error)
            if "queued" in error.lower():
                return jsonify({"message": error, "status": "queued"}), 202
            return jsonify({"error": error}), 400

        return jsonify({
            "id": transaction.id,
            "type": transaction.type.value if hasattr(transaction.type, 'value') else str(transaction.type),
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "account_from": transaction.account_from.name if transaction.account_from else None,
            "account_to": transaction.account_to.name if transaction.account_to else None,
            "currency_to": transaction.currency_to,
            "amount_to": float(transaction.amount_to) if transaction.amount_to else None,
            "exchange_rate": float(transaction.exchange_rate) if transaction.exchange_rate else None,
            "description": transaction.description,
            "date": transaction.date.isoformat(),
            "created_at": transaction.created_at.isoformat(),
        }), 201


@app.route("/transactions/<int:transaction_id>", methods=["PUT"])
@jwt_required()
async def update_transaction(transaction_id: int):
    """
    Update an existing transaction.

    Path params:
        - transaction_id: Transaction ID

    Request body:
        - amount: New amount (optional)
        - description: New description (optional)
        - date: New date (optional)

    Returns:
        - transaction: Updated transaction information
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    amount = data.get("amount")
    description = data.get("description")
    date_str = data.get("date")

    # Parse date if provided
    date = None
    if date_str:
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "Invalid date format. Use ISO format"}), 400

    async with async_session_maker() as session:
        transaction, error = await TransactionService.update_transaction(
            session=session,
            user_id=current_user_id,
            transaction_id=transaction_id,
            amount=amount,
            description=description,
            date=date,
        )

        if error:
            status_code = 404 if "not found" in error.lower() else 400
            return jsonify({"error": error}), status_code

        return jsonify({
            "id": transaction.id,
            "type": transaction.type.value if hasattr(transaction.type, 'value') else str(transaction.type),
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "description": transaction.description,
            "date": transaction.date.isoformat(),
            "updated_at": transaction.created_at.isoformat(),
        }), 200


# ==================== Analytics ====================

@app.route("/analytics", methods=["GET"])
@jwt_required()
async def get_analytics():
    """
    Get financial analytics and dashboard data.

    Query params:
        - date_from: Start date (ISO format) (required)
        - date_to: End date (ISO format) (required)
        - currency: Currency for aggregation (optional, uses all if not specified)

    Returns:
        - total_income: Total income in the period
        - total_expenses: Total expenses in the period
        - net_savings: Net savings (income - expenses)
        - largest_expense: Largest expense transaction
        - largest_income: Largest income transaction
    """
    current_user_id = int(get_jwt_identity())

    date_from_str = request.args.get("date_from")
    date_to_str = request.args.get("date_to")
    currency = request.args.get("currency")

    if not date_from_str or not date_to_str:
        return jsonify({"error": "date_from and date_to are required"}), 400

    try:
        date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
        date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    async with async_session_maker() as session:
        # Get totals
        total_income = await TransactionCRUD.get_total_by_type(
            session, current_user_id, date_from, date_to, TransactionType.INCOME, currency
        )
        total_expenses = await TransactionCRUD.get_total_by_type(
            session, current_user_id, date_from, date_to, TransactionType.EXPENSE, currency
        )

        # Get largest transactions
        largest_expense = await TransactionCRUD.get_largest_in_period(
            session, current_user_id, date_from, date_to, TransactionType.EXPENSE
        )
        largest_income = await TransactionCRUD.get_largest_in_period(
            session, current_user_id, date_from, date_to, TransactionType.INCOME
        )

        return jsonify({
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_savings": float(total_income - total_expenses),
            "largest_expense": {
                "amount": float(largest_expense.amount),
                "currency": largest_expense.currency,
                "description": largest_expense.description,
                "date": largest_expense.date.isoformat(),
            } if largest_expense else None,
            "largest_income": {
                "amount": float(largest_income.amount),
                "currency": largest_income.currency,
                "description": largest_income.description,
                "date": largest_income.date.isoformat(),
            } if largest_income else None,
        }), 200


# ==================== Categories & Merchants (Stub endpoints) ====================

@app.route("/categories", methods=["GET"])
@jwt_required()
async def list_categories():
    """
    List expense categories.

    Note: This is a stub endpoint. Category management is not yet implemented.
    """
    return jsonify({
        "categories": [],
        "message": "Category management not yet implemented"
    }), 200


@app.route("/categories", methods=["POST"])
@jwt_required()
async def create_category():
    """
    Create a new expense category.

    Note: This is a stub endpoint. Category management is not yet implemented.
    """
    return jsonify({
        "error": "Category management not yet implemented"
    }), 501


@app.route("/merchants", methods=["GET"])
@jwt_required()
async def list_merchants():
    """
    List merchants/shops.

    Note: This is a stub endpoint. Merchant management is not yet implemented.
    """
    return jsonify({
        "merchants": [],
        "message": "Merchant management not yet implemented"
    }), 200


@app.route("/merchants", methods=["POST"])
@jwt_required()
async def create_merchant():
    """
    Create a new merchant/shop.

    Note: This is a stub endpoint. Merchant management is not yet implemented.
    """
    return jsonify({
        "error": "Merchant management not yet implemented"
    }), 501


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
