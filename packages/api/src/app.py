import datetime
from flask import Flask

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def get_health():
    return {"healthy": True, "timestamp": datetime.now()}


@app.route("/transactions", methods=["GET"])
def list_transactions():
    """
    Returns the list of transactions of a given user
    Allowed filters:
        * date_from: datetime
        * date_to: datetime
        * category_ids: Optional[list[str]]
        * search_term: str
        * merchant_id: str
    """
    return


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
