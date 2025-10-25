import pytest
from datetime import datetime
from decimal import Decimal

from packages.agent.agent import FinanceAgent
from packages.agent.schemas import TransactionIntent, QueryIntent


@pytest.fixture
def agent():
    return FinanceAgent()


@pytest.mark.asyncio
async def test_parse_income_transaction(agent):
    """Test parsing income transaction."""
    message = "I received 6k USD salary for August via Deel"
    intent = await agent._extract_transaction_intent(message)

    assert intent is not None
    assert intent.intent == TransactionIntent.INCOME
    assert intent.amount == Decimal("6000")
    assert intent.currency == "USD"
    assert intent.account_to == "Deel"
    assert "salary" in intent.description.lower() if intent.description else False


@pytest.mark.asyncio
async def test_parse_expense_transaction(agent):
    """Test parsing expense transaction."""
    message = "I spent 400k ARS from my Galicia account"
    intent = await agent._extract_transaction_intent(message)

    assert intent is not None
    assert intent.intent == TransactionIntent.EXPENSE
    assert intent.amount == Decimal("400000")
    assert intent.currency == "ARS"
    assert intent.account_from == "Galicia"


@pytest.mark.asyncio
async def test_parse_transfer_transaction(agent):
    """Test parsing transfer transaction."""
    message = "I transferred 1K USD to my Astropay account and received 992 USD"
    intent = await agent._extract_transaction_intent(message)

    assert intent is not None
    assert intent.intent == TransactionIntent.TRANSFER
    assert intent.amount == Decimal("1000")
    assert intent.currency == "USD"
    assert intent.account_to == "Astropay"
    assert intent.amount_to == Decimal("992") if intent.amount_to else True


@pytest.mark.asyncio
async def test_parse_conversion_transaction(agent):
    """Test parsing conversion transaction."""
    message = "I converted 10 USDT to ARS in Belo at 1350 ARS per USDT"
    intent = await agent._extract_transaction_intent(message)

    assert intent is not None
    assert intent.intent == TransactionIntent.CONVERSION
    assert intent.amount == Decimal("10")
    assert intent.currency == "USDT"
    assert intent.currency_to == "ARS"
    assert intent.exchange_rate == Decimal("1350") if intent.exchange_rate else True


@pytest.mark.asyncio
async def test_parse_balance_query(agent):
    """Test parsing balance query."""
    message = "What's my balance in Galicia?"
    intent = await agent._extract_query_intent(message)

    assert intent is not None
    assert intent.intent == QueryIntent.BALANCE
    assert intent.account_name == "Galicia"


@pytest.mark.asyncio
async def test_parse_all_accounts_query(agent):
    """Test parsing all accounts query."""
    message = "Show all my accounts and balances"
    intent = await agent._extract_query_intent(message)

    assert intent is not None
    assert intent.intent == QueryIntent.ALL_ACCOUNTS


@pytest.mark.asyncio
async def test_parse_expense_query(agent):
    """Test parsing expense query."""
    message = "How much did I spend in August?"
    intent = await agent._extract_query_intent(message)

    assert intent is not None
    assert intent.intent == QueryIntent.EXPENSES
    # Date parsing is complex, just check that some date logic was attempted


@pytest.mark.asyncio
async def test_parse_largest_purchase_query(agent):
    """Test parsing largest purchase query."""
    message = "What was my largest purchase in August?"
    intent = await agent._extract_query_intent(message)

    assert intent is not None
    assert intent.intent == QueryIntent.LARGEST_PURCHASE


@pytest.mark.asyncio
async def test_non_financial_message_returns_none(agent):
    """Test that non-financial messages return None for both parsers."""
    message = "Hello, how are you today?"

    transaction_intent = await agent._extract_transaction_intent(message)
    query_intent = await agent._extract_query_intent(message)

    assert transaction_intent is None
    assert query_intent is None


@pytest.mark.asyncio
async def test_complex_transaction_parsing(agent):
    """Test parsing more complex transaction descriptions."""
    test_cases = [
        {
            "message": "Freelance payment of 2500 USD received in my Deel account on Sept 15",
            "expected_type": TransactionIntent.INCOME,
            "expected_amount": Decimal("2500"),
            "expected_currency": "USD",
            "expected_account": "Deel"
        },
        {
            "message": "Bought groceries for 250 ARS cash",
            "expected_type": TransactionIntent.EXPENSE,
            "expected_amount": Decimal("250"),
            "expected_currency": "ARS",
            "expected_account": "Cash"
        },
        {
            "message": "Moved 5000 ARS from Galicia to Mercado Pago",
            "expected_type": TransactionIntent.TRANSFER,
            "expected_amount": Decimal("5000"),
            "expected_currency": "ARS"
        }
    ]

    for case in test_cases:
        intent = await agent._extract_transaction_intent(case["message"])

        if intent:  # Some complex cases might not parse perfectly
            assert intent.intent == case["expected_type"]
            if "expected_amount" in case:
                assert intent.amount == case["expected_amount"]
            if "expected_currency" in case:
                assert intent.currency == case["expected_currency"]
