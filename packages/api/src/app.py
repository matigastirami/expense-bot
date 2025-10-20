from datetime import datetime, timedelta
import os
import bcrypt
from flask import Flask, request
from flask.json import jsonify
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from libs.db.crud import TransactionCRUD, UserCRUD
from libs.db.base import async_session_maker


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with salt rounds."""
    salt = bcrypt.gensalt(
        rounds=12
    )  # 12 salt rounds (good balance of security/performance)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


app = Flask(__name__)

# JWT Configuration
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY", "your-secret-key-change-this"
)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Initialize JWT Manager
jwt = JWTManager(app)


@app.route("/health", methods=["GET"])
def get_health():
    return {"healthy": True, "timestamp": datetime.now()}


@app.route("/signin", methods=["POST"])
async def signin():
    email: str = request.json.get("email", None)
    password: str = request.json.get("password", None)

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    async with async_session_maker() as session:
        user = await UserCRUD.get_by_email(session=session, email=email)

        # Check if user exists and verify password
        if user is None or not verify_password(password, user.password):
            return jsonify({"error": "Wrong email or password"}), 401

        access_token = create_access_token(
            identity=user.id, additional_claims={"email": email}
        )

        return jsonify({"access_token": access_token}), 200


@app.route("/signup", methods=["POST"])
async def signup():
    email: str = request.json.get("email", None)
    password: str = request.json.get("password", None)

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    async with async_session_maker() as session:
        # Check if user already exists
        existing_user = await UserCRUD.get_by_email(session=session, email=email)
        if existing_user:
            return jsonify({"error": "User with this email already exists"}), 409

        # Hash password before storing
        hashed_password = hash_password(password)

        # Create new user with hashed password
        user = await UserCRUD.create(
            session=session, email=email, password=hashed_password
        )

        # Generate access token for the new user
        access_token = create_access_token(
            identity=user.id, additional_claims={"email": email}
        )

        return jsonify(
            {
                "message": "User created successfully",
                "access_token": access_token,
                "user": {"id": user.id, "email": user.email},
            }
        ), 201


@app.route("/transactions", methods=["GET"])
@jwt_required()
async def list_transactions():
    """
    Returns the list of transactions of a given user
    Allowed filters:
        * date_from: datetime
        * date_to: datetime
        * category_ids: Optional[list[str]]
        * search_term: str
        * merchant_id: str
    """
    # Get the user ID from the JWT token
    current_user_id = get_jwt_identity()

    async with async_session_maker() as session:
        trxs = await TransactionCRUD.get_by_date_range(
            session=session,
            user_id=current_user_id,  # Use the authenticated user's ID
            start_date=datetime.today().replace(day=1),
            end_date=datetime.now(),
        )

        # Convert transactions to dict for JSON response
        transactions = []
        for trx in trxs:
            transactions.append(
                {
                    "id": trx.id,
                    "amount": float(trx.amount),
                    "date": trx.transaction_date.isoformat(),
                    "description": trx.description,
                }
            )

        return {"transactions": transactions, "count": len(transactions)}


@app.route("/transactions", methods=["PUT"])
def update_transaction():
    """
    Updates a transaction, this can be edited:
        * amount
        * date
        * merchant/shop
        * cateogory
        * Necessity
    """
    return


@app.route("/transactions", methods=["POST"])
def create_transaction():
    """
    Registers a new transaction
    """
    return


@app.route("/categories", methods=["GET"])
def list_categories():
    """
    Return the list of categories for the expenses
    """
    return


@app.route("/categories", methods=["POST"])
def create_category():
    """
    Creates a new category
    """
    return


@app.route("/shops", methods=["GET"])
def list_shops():
    """
    Returns the list of merchants
    """
    return


@app.route("/shops", methods=["POST"])
def create_shop():
    """
    Creates a new merchant
    """
    return


@app.route("/analytics", methods=["GET"])
def get_analytics():
    """
    Returns dashboard related analytics with filters.
    Supported filters:
        * date_from: Datetime
        * date_to: Datetime
    """
    return
