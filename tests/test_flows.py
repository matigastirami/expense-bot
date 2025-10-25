import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from packages.agent.agent import FinanceAgent
from packages.agent.tools.db_tool import QueryBalancesInput


@pytest.fixture
def agent():
    return FinanceAgent()


@pytest.mark.asyncio
async def test_end_to_end_income_flow(agent):
    """Test complete flow from message to database for income."""
    message = "I received 5000 USD freelance payment via Deel"

    response = await agent.process_message(message)

    assert "registered successfully" in response.lower()

    # Verify balance was updated
    balances = await agent.db_tool.query_balances(QueryBalancesInput(account_name="Deel"))
    assert len(balances) == 1
    assert balances[0].balance == Decimal("5000.00")
    assert balances[0].currency == "USD"


@pytest.mark.asyncio
async def test_end_to_end_expense_flow(agent):
    """Test complete flow for expense after setting up balance."""
    # First add some income
    await agent.process_message("I received 2000 USD in my wallet")

    # Then spend some
    response = await agent.process_message("I spent 300 USD from my wallet for groceries")

    assert "registered successfully" in response.lower()

    # Verify balance was updated
    balances = await agent.db_tool.query_balances(QueryBalancesInput(account_name="wallet"))
    assert len(balances) == 1
    assert balances[0].balance == Decimal("1700.00")  # 2000 - 300


@pytest.mark.asyncio
async def test_end_to_end_conversion_with_fx_fetch(agent):
    """Test conversion flow with automatic FX rate fetching."""
    # Mock FX service to return a rate
    with patch('src.agent.tools.fx_tool.fx_service.get_rate') as mock_fx:
        mock_fx.return_value = (Decimal("1400.00"), "mock_source")

        # First add USDT balance
        await agent.process_message("I received 100 USDT in Belo")

        # Then convert without providing rate
        response = await agent.process_message("I converted 50 USDT to ARS in Belo")

        assert "registered successfully" in response.lower()

        # Verify balances
        balances = await agent.db_tool.query_balances(QueryBalancesInput(account_name="Belo"))

        # Should have remaining USDT and new ARS
        currencies = {b.currency: b.balance for b in balances}
        assert "USDT" in currencies
        assert "ARS" in currencies
        assert currencies["USDT"] == Decimal("50.00")  # 100 - 50
        assert currencies["ARS"] == Decimal("70000.00")  # 50 * 1400


@pytest.mark.asyncio
async def test_end_to_end_balance_query(agent):
    """Test balance query flow."""
    # Setup some balances
    await agent.process_message("I received 1000 USD in Astropay")
    await agent.process_message("I received 500000 ARS in Galicia")

    # Query specific account
    response = await agent.process_message("What's my balance in Astropay?")

    assert "Astropay" in response
    assert "USD" in response
    assert "1,000" in response or "1000" in response


@pytest.mark.asyncio
async def test_end_to_end_all_accounts_query(agent):
    """Test all accounts query flow."""
    # Setup multiple accounts
    await agent.process_message("I received 1000 USD in Account1")
    await agent.process_message("I received 2000 USD in Account2")

    # Query all accounts
    response = await agent.process_message("Show all my accounts and balances")

    assert "Account1" in response
    assert "Account2" in response
    assert response.count("USD") >= 2


@pytest.mark.asyncio
async def test_end_to_end_expense_query(agent):
    """Test expense query flow."""
    # Setup some expenses
    await agent.process_message("I received 5000 USD in my wallet")
    await agent.process_message("I spent 200 USD from my wallet for food")
    await agent.process_message("I spent 150 USD from my wallet for transport")

    # Query expenses - this is complex due to date parsing
    response = await agent.process_message("How much did I spend today?")

    # Should mention the total or individual expenses
    assert "USD" in response
    # The exact format will depend on the query processing


@pytest.mark.asyncio
async def test_end_to_end_transfer_flow(agent):
    """Test transfer flow between accounts."""
    # Setup source account
    await agent.process_message("I received 3000 USD in source_account")

    # Transfer to another account
    response = await agent.process_message("I transferred 1000 USD from source_account to dest_account")

    assert "registered successfully" in response.lower()

    # Verify both account balances
    source_balances = await agent.db_tool.query_balances(QueryBalancesInput(account_name="source_account"))
    dest_balances = await agent.db_tool.query_balances(QueryBalancesInput(account_name="dest_account"))

    assert len(source_balances) == 1
    assert len(dest_balances) == 1
    assert source_balances[0].balance == Decimal("2000.00")  # 3000 - 1000
    assert dest_balances[0].balance == Decimal("1000.00")


@pytest.mark.asyncio
async def test_error_handling_insufficient_information():
    """Test error handling when message lacks sufficient information."""
    agent = FinanceAgent()

    # Vague message that shouldn't parse as transaction or query
    response = await agent.process_message("I did something with money")

    # Should either ask for clarification or use general agent processing
    assert len(response) > 0  # Should get some response


@pytest.mark.asyncio
async def test_error_handling_invalid_transaction():
    """Test error handling for invalid transaction data."""
    agent = FinanceAgent()

    # Try to spend from non-existent account
    response = await agent.process_message("I spent 1000 USD from nonexistent_account")

    # Should handle gracefully - might create account with negative balance or error
    assert len(response) > 0


@pytest.mark.asyncio
async def test_monthly_report_flow(agent):
    """Test monthly report generation."""
    # Setup some transactions
    await agent.process_message("I received 5000 USD salary in Deel")
    await agent.process_message("I spent 1200 USD from Deel for rent")
    await agent.process_message("I spent 300 USD from Deel for groceries")

    # Generate report for current month
    now = datetime.now()
    response = await agent.process_message(f"Generate monthly report for {now.year}-{now.month:02d}")

    assert "Monthly Report" in response
    assert "Total Income" in response
    assert "Total Expenses" in response
    assert "Net Savings" in response
