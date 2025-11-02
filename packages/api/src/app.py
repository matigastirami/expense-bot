"""Main Flask application for expense tracker API."""

from datetime import datetime, timedelta
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
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

# CORS Configuration
# Get allowed origins from environment or use defaults
allowed_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []

# Default origins for development
default_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://45ae773014be.ngrok-free.app",
]

# Combine default and custom origins
all_origins = default_origins + [origin.strip() for origin in allowed_origins if origin.strip()]

print(f"CORS allowed origins: {all_origins}")

CORS(app, resources={
    r"/*": {
        "origins": all_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
    }
})

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


@app.route("/auth/telegram", methods=["POST"])
async def telegram_auth():
    """
    Authenticate or register user via Telegram Login Widget.

    Request body:
        - id: Telegram user ID
        - first_name: User's first name
        - last_name: (Optional) User's last name
        - username: (Optional) Telegram username
        - photo_url: (Optional) Profile photo URL
        - auth_date: Authentication timestamp
        - hash: Security hash from Telegram

    Returns:
        - access_token: JWT token for authentication
        - user: User information
        - is_new_user: Boolean indicating if this is a new registration
    """
    import hashlib
    import hmac

    print("=== Telegram Auth Request Started ===")

    data = request.get_json()
    print(f"Received data: {data}")

    # Extract Telegram data
    telegram_id = str(data.get("id"))
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    username = data.get("username")
    auth_date = data.get("auth_date")
    hash_value = data.get("hash")

    print(f"Extracted fields - telegram_id: {telegram_id}, first_name: {first_name}, username: {username}, auth_date: {auth_date}, hash present: {bool(hash_value)}")

    if not telegram_id or not first_name or not auth_date or not hash_value:
        missing_fields = []
        if not telegram_id:
            missing_fields.append("id")
        if not first_name:
            missing_fields.append("first_name")
        if not auth_date:
            missing_fields.append("auth_date")
        if not hash_value:
            missing_fields.append("hash")

        error_msg = f"Missing required Telegram authentication data: {', '.join(missing_fields)}"
        print(f"ERROR: {error_msg}")
        return jsonify({"error": error_msg}), 400

    # Verify Telegram authentication (security check)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN environment variable not set")
        return jsonify({"error": "Telegram bot not configured"}), 500

    print(f"Bot token configured (length: {len(bot_token)})")

    # Create data check string
    check_data = []
    for key in sorted(data.keys()):
        if key != "hash":
            check_data.append(f"{key}={data[key]}")
    data_check_string = "\n".join(check_data)

    print(f"Data check string:\n{data_check_string}")

    # Create secret key
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    print(f"Secret key created (length: {len(secret_key)})")

    # Calculate hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    print(f"Calculated hash: {calculated_hash}")
    print(f"Received hash:   {hash_value}")
    print(f"Hash match: {calculated_hash == hash_value}")

    # Verify hash
    if calculated_hash != hash_value:
        print("ERROR: Hash verification failed - invalid Telegram authentication")
        return jsonify({"error": "Invalid Telegram authentication"}), 401

    print("Hash verification successful")

    # Check if auth_date is recent (within 24 hours)
    import time
    current_time = int(time.time())
    auth_age = current_time - int(auth_date)
    print(f"Auth timestamp age: {auth_age} seconds ({auth_age / 3600:.2f} hours)")

    if auth_age > 86400:  # 24 hours
        print(f"ERROR: Authentication data is too old ({auth_age} seconds)")
        return jsonify({"error": "Authentication data is too old"}), 401

    print("Auth timestamp validation successful")

    async with async_session_maker() as session:
        print(f"Looking up user by telegram_id: {telegram_id}")

        # Check if user exists
        user = await UserService.get_user_by_telegram_id(session, telegram_id)
        is_new_user = user is None

        print(f"User lookup result - is_new_user: {is_new_user}, user found: {user is not None}")

        if not user:
            print(f"Creating new user - telegram_id: {telegram_id}, first_name: {first_name}, last_name: {last_name}, username: {username}")

            # Create new user with Telegram data
            from libs.db.crud import UserCRUD
            try:
                user = await UserCRUD.create(
                    session=session,
                    telegram_user_id=telegram_id,
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                )
                print(f"User created successfully - user_id: {user.id}")
            except Exception as e:
                print(f"ERROR creating user: {str(e)}")
                print(f"Exception type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": f"Failed to create user: {str(e)}"}), 500
        else:
            print(f"Existing user found - user_id: {user.id}, telegram_id: {user.telegram_user_id}")

        # Generate access token
        print(f"Generating access token for user_id: {user.id}")
        try:
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={
                    "telegram_id": user.telegram_user_id,
                    "email": user.email
                }
            )
            print("Access token generated successfully")
        except Exception as e:
            print(f"ERROR generating access token: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Failed to generate token: {str(e)}"}), 500

        response_data = {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "telegram_user_id": user.telegram_user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "email": user.email,
            },
            "is_new_user": is_new_user
        }

        print(f"Telegram auth successful - returning response for user_id: {user.id}, is_new_user: {is_new_user}")
        print("=== Telegram Auth Request Completed Successfully ===")

        return jsonify(response_data), 200


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


@app.route("/accounts/<int:account_id>", methods=["PUT"])
@jwt_required()
async def update_account(account_id: int):
    """
    Update an existing account.

    Path params:
        - account_id: Account ID

    Request body:
        - name: Account name (optional)
        - type: Account type (optional)
        - track_balance: Whether to track balance (optional)

    Returns:
        - account: Updated account information
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    async with async_session_maker() as session:
        from sqlalchemy import select, update
        from libs.db.models import Account

        # Verify account exists and belongs to user
        result = await session.execute(
            select(Account).where(
                Account.id == account_id,
                Account.user_id == current_user_id
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return jsonify({"error": "Account not found"}), 404

        # Update fields if provided
        update_data = {}
        if "name" in data:
            update_data["name"] = data["name"]
        if "type" in data:
            update_data["type"] = data["type"]
        if "track_balance" in data:
            update_data["track_balance"] = data["track_balance"]

        if update_data:
            await session.execute(
                update(Account).where(Account.id == account_id).values(**update_data)
            )
            await session.commit()
            await session.refresh(account)

        return jsonify({
            "id": account.id,
            "name": account.name,
            "type": account.type,
            "track_balance": account.track_balance,
            "created_at": account.created_at.isoformat(),
        }), 200


@app.route("/accounts/<int:account_id>", methods=["DELETE"])
@jwt_required()
async def delete_account(account_id: int):
    """
    Delete an account.

    Path params:
        - account_id: Account ID

    Returns:
        - message: Success message
    """
    current_user_id = int(get_jwt_identity())

    async with async_session_maker() as session:
        from sqlalchemy import select, delete
        from libs.db.models import Account

        # Verify account exists and belongs to user
        result = await session.execute(
            select(Account).where(
                Account.id == account_id,
                Account.user_id == current_user_id
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return jsonify({"error": "Account not found"}), 404

        # Delete the account
        await session.execute(
            delete(Account).where(Account.id == account_id)
        )
        await session.commit()

        return jsonify({"message": "Account deleted successfully"}), 200


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
    Update an existing transaction - all fields are editable.

    Path params:
        - transaction_id: Transaction ID

    Request body (all optional):
        - amount: New amount
        - description: New description
        - date: New date (ISO format)
        - type: New transaction type (income, expense, transfer, conversion)
        - currency: New currency
        - account_from: New source account name
        - account_to: New destination account name
        - category_id: New category ID
        - merchant_id: New merchant ID
        - is_necessary: New necessity flag (true/false)
        - currency_to: New destination currency
        - amount_to: New destination amount
        - exchange_rate: New exchange rate

    Returns:
        - transaction: Updated transaction information
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    # Extract all possible fields
    amount = data.get("amount")
    description = data.get("description")
    date_str = data.get("date")
    transaction_type = data.get("type")
    currency = data.get("currency")
    account_from = data.get("account_from")
    account_to = data.get("account_to")
    category_id = data.get("category_id")
    merchant_id = data.get("merchant_id")
    is_necessary = data.get("is_necessary")
    currency_to = data.get("currency_to")
    amount_to = data.get("amount_to")
    exchange_rate = data.get("exchange_rate")

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
            transaction_type=transaction_type,
            currency=currency,
            account_from=account_from,
            account_to=account_to,
            category_id=category_id,
            merchant_id=merchant_id,
            is_necessary=is_necessary,
            currency_to=currency_to,
            amount_to=amount_to,
            exchange_rate=exchange_rate,
        )

        if error:
            status_code = 404 if "not found" in error.lower() else 400
            return jsonify({"error": error}), status_code

        # Refresh relationships to include category and merchant
        await session.refresh(transaction, ["category", "merchant", "account_from", "account_to"])

        return jsonify({
            "id": transaction.id,
            "type": transaction.type.value if hasattr(transaction.type, 'value') else str(transaction.type),
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "account_from": transaction.account_from.name if transaction.account_from else None,
            "account_to": transaction.account_to.name if transaction.account_to else None,
            "category_id": transaction.category_id,
            "category": transaction.category.name if transaction.category else None,
            "merchant_id": transaction.merchant_id,
            "merchant": transaction.merchant.name if transaction.merchant else None,
            "is_necessary": transaction.is_necessary,
            "currency_to": transaction.currency_to,
            "amount_to": float(transaction.amount_to) if transaction.amount_to else None,
            "exchange_rate": float(transaction.exchange_rate) if transaction.exchange_rate else None,
            "description": transaction.description,
            "date": transaction.date.isoformat(),
            "updated_at": transaction.created_at.isoformat(),
        }), 200


@app.route("/transactions/<int:transaction_id>", methods=["DELETE"])
@jwt_required()
async def delete_transaction(transaction_id: int):
    """
    Delete a transaction.

    Path params:
        - transaction_id: Transaction ID

    Returns:
        - message: Success message
    """
    current_user_id = int(get_jwt_identity())

    async with async_session_maker() as session:
        from sqlalchemy import select, delete
        from libs.db.models import Transaction

        # Verify transaction exists and belongs to user
        result = await session.execute(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == current_user_id
            )
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        # Delete the transaction
        await session.execute(
            delete(Transaction).where(Transaction.id == transaction_id)
        )
        await session.commit()

        return jsonify({"message": "Transaction deleted successfully"}), 200


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


# ==================== Categories ====================

@app.route("/categories", methods=["GET"])
@jwt_required()
async def list_categories():
    """
    List all categories for the authenticated user.

    Returns:
        - categories: List of categories with id, name, type, and created_at
    """
    current_user_id = int(get_jwt_identity())

    async with async_session_maker() as session:
        from libs.db.crud import CategoryCRUD

        categories = await CategoryCRUD.get_all(session, current_user_id)

        return jsonify({
            "categories": [
                {
                    "id": category.id,
                    "name": category.name,
                    "type": category.type,
                    "created_at": category.created_at.isoformat(),
                }
                for category in categories
            ]
        }), 200


@app.route("/categories", methods=["POST"])
@jwt_required()
async def create_category():
    """
    Create a new category for the authenticated user.

    Request body:
        - name: Category name (required)
        - type: Category type (income or expense) (required)

    Returns:
        - id: Created category ID
        - name: Category name
        - type: Category type
        - created_at: Creation timestamp
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    name = data.get("name")
    category_type = data.get("type")

    if not name or not category_type:
        return jsonify({"error": "name and type are required"}), 400

    if category_type not in ["income", "expense"]:
        return jsonify({"error": "type must be 'income' or 'expense'"}), 400

    async with async_session_maker() as session:
        from libs.db.crud import CategoryCRUD

        # Check if category with same name already exists
        existing = await CategoryCRUD.get_by_name(session, current_user_id, name)
        if existing:
            return jsonify({"error": "Category with this name already exists"}), 400

        category = await CategoryCRUD.create(session, current_user_id, name, category_type)

        return jsonify({
            "id": category.id,
            "name": category.name,
            "type": category.type,
            "created_at": category.created_at.isoformat(),
        }), 201


@app.route("/categories/<int:category_id>", methods=["PUT"])
@jwt_required()
async def update_category(category_id: int):
    """
    Update an existing category.

    Path params:
        - category_id: Category ID

    Request body:
        - name: New category name (optional)
        - type: New category type (optional)

    Returns:
        - id: Category ID
        - name: Category name
        - type: Category type
        - created_at: Creation timestamp
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    name = data.get("name")
    category_type = data.get("type")

    if category_type and category_type not in ["income", "expense"]:
        return jsonify({"error": "type must be 'income' or 'expense'"}), 400

    async with async_session_maker() as session:
        from libs.db.crud import CategoryCRUD

        # Check if category with same name already exists (excluding current category)
        if name:
            existing = await CategoryCRUD.get_by_name(session, current_user_id, name)
            if existing and existing.id != category_id:
                return jsonify({"error": "Category with this name already exists"}), 400

        category = await CategoryCRUD.update(
            session, category_id, current_user_id, name, category_type
        )

        if not category:
            return jsonify({"error": "Category not found"}), 404

        return jsonify({
            "id": category.id,
            "name": category.name,
            "type": category.type,
            "created_at": category.created_at.isoformat(),
        }), 200


@app.route("/categories/<int:category_id>", methods=["DELETE"])
@jwt_required()
async def delete_category(category_id: int):
    """
    Delete a category.

    Path params:
        - category_id: Category ID

    Returns:
        - message: Success message
    """
    current_user_id = int(get_jwt_identity())

    async with async_session_maker() as session:
        from libs.db.crud import CategoryCRUD

        deleted = await CategoryCRUD.delete(session, category_id, current_user_id)

        if not deleted:
            return jsonify({"error": "Category not found"}), 404

        return jsonify({"message": "Category deleted successfully"}), 200


# ==================== Merchants ====================

@app.route("/merchants", methods=["GET"])
@jwt_required()
async def list_merchants():
    """
    List all merchants for the authenticated user.

    Returns:
        - merchants: List of merchants with id, name, and created_at
    """
    current_user_id = int(get_jwt_identity())

    async with async_session_maker() as session:
        from libs.db.crud import MerchantCRUD

        merchants = await MerchantCRUD.get_all(session, current_user_id)

        return jsonify({
            "merchants": [
                {
                    "id": merchant.id,
                    "name": merchant.name,
                    "created_at": merchant.created_at.isoformat(),
                }
                for merchant in merchants
            ]
        }), 200


@app.route("/merchants", methods=["POST"])
@jwt_required()
async def create_merchant():
    """
    Create a new merchant for the authenticated user.

    Request body:
        - name: Merchant name (required)

    Returns:
        - id: Created merchant ID
        - name: Merchant name
        - created_at: Creation timestamp
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    name = data.get("name")

    if not name:
        return jsonify({"error": "name is required"}), 400

    async with async_session_maker() as session:
        from libs.db.crud import MerchantCRUD

        # Check if merchant with same name already exists
        existing = await MerchantCRUD.get_by_name(session, current_user_id, name)
        if existing:
            return jsonify({"error": "Merchant with this name already exists"}), 400

        merchant = await MerchantCRUD.create(session, current_user_id, name)

        return jsonify({
            "id": merchant.id,
            "name": merchant.name,
            "created_at": merchant.created_at.isoformat(),
        }), 201


@app.route("/merchants/<int:merchant_id>", methods=["PUT"])
@jwt_required()
async def update_merchant(merchant_id: int):
    """
    Update an existing merchant.

    Path params:
        - merchant_id: Merchant ID

    Request body:
        - name: New merchant name (required)

    Returns:
        - id: Merchant ID
        - name: Merchant name
        - created_at: Creation timestamp
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    name = data.get("name")

    if not name:
        return jsonify({"error": "name is required"}), 400

    async with async_session_maker() as session:
        from libs.db.crud import MerchantCRUD

        # Check if merchant with same name already exists (excluding current merchant)
        existing = await MerchantCRUD.get_by_name(session, current_user_id, name)
        if existing and existing.id != merchant_id:
            return jsonify({"error": "Merchant with this name already exists"}), 400

        merchant = await MerchantCRUD.update(
            session, merchant_id, current_user_id, name
        )

        if not merchant:
            return jsonify({"error": "Merchant not found"}), 404

        return jsonify({
            "id": merchant.id,
            "name": merchant.name,
            "created_at": merchant.created_at.isoformat(),
        }), 200


@app.route("/merchants/<int:merchant_id>", methods=["DELETE"])
@jwt_required()
async def delete_merchant(merchant_id: int):
    """
    Delete a merchant.

    Path params:
        - merchant_id: Merchant ID

    Returns:
        - message: Success message
    """
    current_user_id = int(get_jwt_identity())

    async with async_session_maker() as session:
        from libs.db.crud import MerchantCRUD

        deleted = await MerchantCRUD.delete(session, merchant_id, current_user_id)

        if not deleted:
            return jsonify({"error": "Merchant not found"}), 404

        return jsonify({"message": "Merchant deleted successfully"}), 200


@app.route("/link-telegram", methods=["POST"])
@jwt_required()
async def link_telegram():
    """
    Link a Telegram account to the authenticated user.

    Request body:
        - telegram_user_id: Telegram user ID to link

    Returns:
        - message: Success message
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    telegram_user_id = data.get("telegram_user_id")

    if not telegram_user_id:
        return jsonify({"error": "telegram_user_id is required"}), 400

    async with async_session_maker() as session:
        from sqlalchemy import select, update
        from libs.db.models import User

        # Check if telegram_user_id is already linked to another account
        result = await session.execute(
            select(User).where(User.telegram_user_id == telegram_user_id)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user and existing_user.id != current_user_id:
            return jsonify({
                "error": "This Telegram account is already linked to another user"
            }), 400

        # Link telegram account to current user
        await session.execute(
            update(User)
            .where(User.id == current_user_id)
            .values(telegram_user_id=telegram_user_id)
        )
        await session.commit()

        return jsonify({
            "message": "Telegram account linked successfully"
        }), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
