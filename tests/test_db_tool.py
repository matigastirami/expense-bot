import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from packages.agent.tools.db_tool import DbTool, RegisterTransactionInput, QueryBalancesInput, QueryTransactionsInput
from libs.db.crud import AccountCRUD
from libs.db.models import AccountType


@pytest.fixture
def db_tool():
    return DbTool()


@pytest.mark.asyncio
async def test_register_income_transaction(db_tool, async_session):
    """Test registering an income transaction."""
    input_data = RegisterTransactionInput(
        transaction_type="income",
        amount=1000.0,
        currency="USD",
        account_to="Test Account",
        description="Test income"
    )

    result = await db_tool.register_transaction(input_data)
    assert "registered successfully" in result

    # Verify account was created and balance updated
    account = await AccountCRUD.get_by_name(async_session, "Test Account")
    assert account is not None
    assert len(account.balances) == 1
    assert account.balances[0].balance == Decimal("1000.00")
    assert account.balances[0].currency == "USD"


@pytest.mark.asyncio
async def test_register_expense_transaction(db_tool, async_session, sample_account_with_balance):
    """Test registering an expense transaction."""
    input_data = RegisterTransactionInput(
        transaction_type="expense",
        amount=200.0,
        currency="USD",
        account_from=sample_account_with_balance.name,
        description="Test expense"
    )

    result = await db_tool.register_transaction(input_data)
    assert "registered successfully" in result

    # Verify balance was decreased
    await async_session.refresh(sample_account_with_balance)
    balance = next((b for b in sample_account_with_balance.balances if b.currency == "USD"), None)
    assert balance is not None
    assert balance.balance == Decimal("800.00")  # 1000 - 200


@pytest.mark.asyncio
async def test_register_transfer_transaction(db_tool, async_session):
    """Test registering a transfer transaction."""
    # Create source account with balance
    source_account = await AccountCRUD.create(async_session, "Source", AccountType.BANK)
    await async_session.execute(
        "INSERT INTO account_balances (account_id, currency, balance) VALUES (?, ?, ?)",
        (source_account.id, "USD", Decimal("1000.00"))
    )

    input_data = RegisterTransactionInput(
        transaction_type="transfer",
        amount=300.0,
        currency="USD",
        account_from="Source",
        account_to="Destination",
        amount_to=295.0,  # With fees
        description="Test transfer"
    )

    result = await db_tool.register_transaction(input_data)
    assert "registered successfully" in result


@pytest.mark.asyncio
async def test_register_conversion_transaction(db_tool, async_session):
    """Test registering a conversion transaction."""
    input_data = RegisterTransactionInput(
        transaction_type="conversion",
        amount=100.0,
        currency="USDT",
        account_from="Belo",
        amount_to=135000.0,
        currency_to="ARS",
        exchange_rate=1350.0,
        description="USDT to ARS conversion"
    )

    result = await db_tool.register_transaction(input_data)
    assert "registered successfully" in result


@pytest.mark.asyncio
async def test_query_balances_all_accounts(db_tool, async_session):
    """Test querying all account balances."""
    # Setup test data
    await db_tool.register_transaction(RegisterTransactionInput(
        transaction_type="income",
        amount=1000.0,
        currency="USD",
        account_to="Account1"
    ))

    await db_tool.register_transaction(RegisterTransactionInput(
        transaction_type="income",
        amount=50000.0,
        currency="ARS",
        account_to="Account2"
    ))

    # Query all balances
    balances = await db_tool.query_balances(QueryBalancesInput())

    assert len(balances) == 2
    account_names = {b.account_name for b in balances}
    assert "Account1" in account_names
    assert "Account2" in account_names


@pytest.mark.asyncio
async def test_query_balances_specific_account(db_tool, async_session):
    """Test querying specific account balance."""
    await db_tool.register_transaction(RegisterTransactionInput(
        transaction_type="income",
        amount=500.0,
        currency="USD",
        account_to="Specific Account"
    ))

    balances = await db_tool.query_balances(QueryBalancesInput(account_name="Specific Account"))

    assert len(balances) == 1
    assert balances[0].account_name == "Specific Account"
    assert balances[0].balance == Decimal("500.00")


@pytest.mark.asyncio
async def test_query_transactions_by_date_range(db_tool, async_session):
    """Test querying transactions by date range."""
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)

    # Register transaction with specific date
    await db_tool.register_transaction(RegisterTransactionInput(
        transaction_type="expense",
        amount=100.0,
        currency="USD",
        account_from="Test Account",
        date=yesterday
    ))

    # Query transactions
    transactions = await db_tool.query_transactions(QueryTransactionsInput(
        start_date=yesterday - timedelta(hours=1),
        end_date=yesterday + timedelta(hours=1)
    ))

    assert len(transactions) == 1
    assert transactions[0].type == "expense"
    assert transactions[0].amount == Decimal("100.00")


@pytest.mark.asyncio
async def test_get_largest_transaction(db_tool, async_session):
    """Test getting largest transaction in period."""
    now = datetime.utcnow()

    # Register multiple transactions
    amounts = [100.0, 500.0, 250.0]
    for amount in amounts:
        await db_tool.register_transaction(RegisterTransactionInput(
            transaction_type="expense",
            amount=amount,
            currency="USD",
            account_from="Test Account"
        ))

    largest = await db_tool.get_largest_transaction(
        now - timedelta(hours=1),
        now + timedelta(hours=1),
        "expense"
    )

    assert largest is not None
    assert largest.amount == Decimal("500.00")


@pytest.mark.asyncio
async def test_error_handling_insufficient_balance(db_tool):
    """Test error handling for insufficient balance."""
    input_data = RegisterTransactionInput(
        transaction_type="expense",
        amount=2000.0,  # More than available
        currency="USD",
        account_from="Empty Account"
    )

    result = await db_tool.register_transaction(input_data)
    # Should handle gracefully, possibly creating negative balance or error
