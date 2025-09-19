from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.agent.schemas import BalanceInfo, MonthlyReport, TransactionInfo
from src.db.base import async_session_maker
from src.db.crud import AccountBalanceCRUD, AccountCRUD, ExchangeRateCRUD, PendingTransactionCRUD, TransactionCRUD
from src.db.models import Account, AccountBalance, AccountType, BalanceTrackingMode, TransactionType, User
from src.reports.pdf_service import PDFReportService


class RegisterTransactionInput(BaseModel):
    transaction_type: str = Field(..., description="Type: income, expense, transfer, conversion")
    amount: float = Field(..., description="Transaction amount", gt=0)
    currency: str = Field(..., description="Currency code")
    account_from: Optional[str] = Field(None, description="Source account name")
    account_to: Optional[str] = Field(None, description="Destination account name")
    amount_to: Optional[float] = Field(None, description="Destination amount for conversions")
    currency_to: Optional[str] = Field(None, description="Destination currency")
    exchange_rate: Optional[float] = Field(None, description="Exchange rate")
    description: Optional[str] = Field(None, description="Transaction description")
    date: Optional[datetime] = Field(None, description="Transaction date")
    user_id: Optional[int] = Field(None, description="User ID for tracking")


class QueryBalancesInput(BaseModel):
    account_name: Optional[str] = Field(None, description="Specific account name")


class QueryTransactionsInput(BaseModel):
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    account_name: Optional[str] = Field(None, description="Specific account name")
    transaction_type: Optional[str] = Field(None, description="Transaction type filter")


class QueryMonthlyReportInput(BaseModel):
    month: int = Field(..., description="Month (1-12)")
    year: int = Field(..., description="Year")


class DbTool(BaseTool):
    name: str = "db_tool"
    description: str = "Database tool for financial operations: register transactions, query balances, and generate reports"

    async def _should_track_balance(self, session: AsyncSession, user_id: int, account_id: int) -> bool:
        """Check if balance tracking should be enabled for this account."""
        # Get user's balance tracking mode
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()

        # Get account's specific setting
        account_result = await session.execute(
            select(Account).where(Account.id == account_id)
        )
        account = account_result.scalar_one()

        # Debug logging - we'll return this info for display
        debug_info = {
            'user_mode': str(user.balance_tracking_mode),
            'user_mode_type': str(type(user.balance_tracking_mode)),
            'account_track': account.track_balance,
            'should_track': None
        }

        # Account-specific setting overrides user setting
        if account.track_balance is not None:
            result = account.track_balance
        else:
            # Fall back to user's general setting - compare as strings to be safe
            result = str(user.balance_tracking_mode) == "strict"

        debug_info['should_track'] = result

        # Store debug info for later use (we'll access this in transaction processing)
        self._last_debug_info = debug_info

        return result

    async def register_transaction(self, input_data: RegisterTransactionInput) -> str:
        async with async_session_maker() as session:
            try:
                # Convert transaction type
                transaction_type = TransactionType(input_data.transaction_type.lower())

                # Get or create accounts
                account_from = None
                account_to = None

                if input_data.account_from:
                    account_from = await AccountCRUD.get_or_create(
                        session, input_data.user_id, input_data.account_from, AccountType.OTHER
                    )

                if input_data.account_to:
                    account_to = await AccountCRUD.get_or_create(
                        session, input_data.user_id, input_data.account_to, AccountType.OTHER
                    )

                # Process transaction based on type
                date = input_data.date or datetime.utcnow()
                amount = Decimal(str(input_data.amount))

                if transaction_type == TransactionType.INCOME:
                    if not account_to:
                        raise ValueError("Income requires destination account")

                    # Handle currency conversion for income
                    account_currency, converted_amount, conversion_success = await self._handle_currency_conversion(
                        session, account_to.id, input_data.currency, amount
                    )

                    if not conversion_success:
                        # Exchange rate unavailable - queue transaction for later processing
                        await PendingTransactionCRUD.create(
                            session=session,
                            transaction_type=transaction_type,
                            currency=input_data.currency,
                            amount=amount,
                            date=date,
                            user_id=input_data.user_id,
                            account_to_id=account_to.id,
                            description=input_data.description,
                            last_error=f"Exchange rate unavailable for {input_data.currency}/{account_currency}",
                        )
                        return f"⏳ Transaction queued - Exchange rate for {input_data.currency}/{account_currency} temporarily unavailable. Will retry automatically every 2 hours."

                    # Only update balance if tracking is enabled
                    if await self._should_track_balance(session, input_data.user_id, account_to.id):
                        await AccountBalanceCRUD.add_to_balance(
                            session, account_to.id, account_currency, converted_amount
                        )

                    await TransactionCRUD.create(
                        session=session,
                        user_id=input_data.user_id,
                        transaction_type=transaction_type,
                        currency=input_data.currency,
                        amount=amount,
                        account_to_id=account_to.id,
                        description=input_data.description,
                        date=date,
                    )

                elif transaction_type == TransactionType.EXPENSE:
                    if not account_from:
                        raise ValueError("Expense requires source account")

                    # Check if account has existing balance in a different currency
                    account_currency, converted_amount, conversion_success = await self._handle_currency_conversion(
                        session, account_from.id, input_data.currency, amount
                    )

                    if not conversion_success:
                        # Exchange rate unavailable - queue transaction for later processing
                        await PendingTransactionCRUD.create(
                            session=session,
                            transaction_type=transaction_type,
                            currency=input_data.currency,
                            amount=amount,
                            date=date,
                            user_id=input_data.user_id,
                            account_from_id=account_from.id,
                            description=input_data.description,
                            last_error=f"Exchange rate unavailable for {input_data.currency}/{account_currency}",
                        )
                        return f"⏳ Transaction queued - Exchange rate for {input_data.currency}/{account_currency} temporarily unavailable. Will retry automatically every 2 hours."

                    # Only update balance if tracking is enabled
                    if await self._should_track_balance(session, input_data.user_id, account_from.id):
                        await AccountBalanceCRUD.add_to_balance(
                            session, account_from.id, account_currency, -converted_amount
                        )

                    await TransactionCRUD.create(
                        session=session,
                        user_id=input_data.user_id,
                        transaction_type=transaction_type,
                        currency=input_data.currency,
                        amount=amount,
                        account_from_id=account_from.id,
                        description=input_data.description,
                        date=date,
                    )

                elif transaction_type == TransactionType.TRANSFER:
                    if not account_from or not account_to:
                        raise ValueError("Transfer requires both source and destination accounts")

                    # Handle currency conversion for source account
                    from_currency, from_converted_amount, from_conversion_success = await self._handle_currency_conversion(
                        session, account_from.id, input_data.currency, amount
                    )

                    # Add to destination (use amount_to if different due to fees)
                    destination_amount = Decimal(str(input_data.amount_to)) if input_data.amount_to else amount
                    destination_currency = input_data.currency_to or input_data.currency

                    # Handle currency conversion for destination account
                    to_currency, to_converted_amount, to_conversion_success = await self._handle_currency_conversion(
                        session, account_to.id, destination_currency, destination_amount
                    )

                    if not from_conversion_success or not to_conversion_success:
                        # Exchange rate unavailable - queue transaction for later processing
                        failed_pair = ""
                        if not from_conversion_success:
                            failed_pair += f"{input_data.currency}/{from_currency}"
                        if not to_conversion_success:
                            if failed_pair:
                                failed_pair += " and "
                            failed_pair += f"{destination_currency}/{to_currency}"

                        await PendingTransactionCRUD.create(
                            session=session,
                            transaction_type=transaction_type,
                            currency=input_data.currency,
                            amount=amount,
                            date=date,
                            user_id=input_data.user_id,
                            account_from_id=account_from.id,
                            account_to_id=account_to.id,
                            currency_to=destination_currency,
                            amount_to=destination_amount,
                            description=input_data.description,
                            last_error=f"Exchange rate unavailable for {failed_pair}",
                        )
                        return f"⏳ Transaction queued - Exchange rate for {failed_pair} temporarily unavailable. Will retry automatically every 2 hours."

                    # Remove from source (only if tracking enabled)
                    if await self._should_track_balance(session, input_data.user_id, account_from.id):
                        await AccountBalanceCRUD.add_to_balance(
                            session, account_from.id, from_currency, -from_converted_amount
                        )

                    # Add to destination (only if tracking enabled)
                    if await self._should_track_balance(session, input_data.user_id, account_to.id):
                        await AccountBalanceCRUD.add_to_balance(
                            session, account_to.id, to_currency, to_converted_amount
                        )

                    await TransactionCRUD.create(
                        session=session,
                        user_id=input_data.user_id,
                        transaction_type=transaction_type,
                        currency=input_data.currency,
                        amount=amount,
                        account_from_id=account_from.id,
                        account_to_id=account_to.id,
                        currency_to=destination_currency,
                        amount_to=destination_amount,
                        exchange_rate=Decimal(str(input_data.exchange_rate)) if input_data.exchange_rate else None,
                        description=input_data.description,
                        date=date,
                    )

                elif transaction_type == TransactionType.CONVERSION:
                    if not account_from or not input_data.currency_to or not input_data.amount_to:
                        raise ValueError("Conversion requires account, target currency, and target amount")

                    # If no destination account specified, use same account as source
                    if not account_to:
                        account_to = account_from

                    # Remove source currency (only if tracking enabled)
                    if await self._should_track_balance(session, input_data.user_id, account_from.id):
                        await AccountBalanceCRUD.add_to_balance(
                            session, account_from.id, input_data.currency, -amount
                        )

                    # Add destination currency (only if tracking enabled)
                    amount_to = Decimal(str(input_data.amount_to))
                    if await self._should_track_balance(session, input_data.user_id, account_to.id):
                        await AccountBalanceCRUD.add_to_balance(
                            session, account_to.id, input_data.currency_to, amount_to
                        )

                    await TransactionCRUD.create(
                        session=session,
                        user_id=input_data.user_id,
                        transaction_type=transaction_type,
                        currency=input_data.currency,
                        amount=amount,
                        account_from_id=account_from.id,
                        account_to_id=account_to.id,
                        currency_to=input_data.currency_to,
                        amount_to=amount_to,
                        exchange_rate=Decimal(str(input_data.exchange_rate)) if input_data.exchange_rate else None,
                        description=input_data.description,
                        date=date,
                    )

                return f"✅ {transaction_type.value.title()} registered successfully"

            except Exception as e:
                await session.rollback()
                # Include debug info if available
                debug_str = ""
                if hasattr(self, '_last_debug_info') and self._last_debug_info:
                    debug_info = self._last_debug_info
                    debug_str = f"\n🔍 DEBUG INFO:\n" \
                              f"• User mode: {debug_info['user_mode']} ({debug_info['user_mode_type']})\n" \
                              f"• Account track_balance: {debug_info['account_track']}\n" \
                              f"• Should track: {debug_info['should_track']}"
                return f"❌ Error registering transaction: {str(e)}{debug_str}"

    async def query_balances(self, input_data: QueryBalancesInput, user_id: int) -> List[BalanceInfo]:
        async with async_session_maker() as session:
            if input_data.account_name:
                account = await AccountCRUD.get_by_name(session, user_id, input_data.account_name)
                if not account:
                    return []
                accounts = [account]
            else:
                accounts = await AccountCRUD.get_all_with_balances(session, user_id)

            balances = []
            for account in accounts:
                # Check if this account tracks balances
                should_track = await self._should_track_balance(session, user_id, account.id)

                if should_track:
                    # Show actual balances for tracked accounts
                    for balance in account.balances:
                        if balance.balance > 0:  # Only show non-zero balances
                            balances.append(
                                BalanceInfo(
                                    account_name=account.name,
                                    currency=balance.currency,
                                    balance=balance.balance,
                                    is_tracked=True
                                )
                            )
                else:
                    # Show "Not tracked" status for non-tracked accounts
                    balances.append(
                        BalanceInfo(
                            account_name=account.name,
                            currency="N/A",
                            balance=Decimal("0"),  # Use 0 as placeholder, will be handled in formatting
                            is_tracked=False  # We'll need to add this field
                        )
                    )

            return balances

    async def query_transactions(self, input_data: QueryTransactionsInput, user_id: int) -> List[TransactionInfo]:
        async with async_session_maker() as session:
            account_id = None
            if input_data.account_name:
                account = await AccountCRUD.get_by_name(session, user_id, input_data.account_name)
                if account:
                    account_id = account.id

            transactions = await TransactionCRUD.get_by_date_range(
                session, user_id, input_data.start_date, input_data.end_date, account_id
            )

            # Filter by type if specified
            if input_data.transaction_type:
                transaction_type = TransactionType(input_data.transaction_type.lower())
                transactions = [t for t in transactions if t.type == transaction_type]

            return [
                TransactionInfo(
                    id=t.id,
                    type=t.type.value if hasattr(t.type, 'value') else str(t.type),
                    amount=t.amount,
                    currency=t.currency,
                    account_from=t.account_from.name if t.account_from else None,
                    account_to=t.account_to.name if t.account_to else None,
                    description=t.description,
                    date=t.date,
                )
                for t in transactions
            ]

    async def get_largest_transaction(self, user_id: int, start_date: datetime, end_date: datetime, transaction_type: Optional[str] = None) -> Optional[TransactionInfo]:
        async with async_session_maker() as session:
            tx_type = TransactionType(transaction_type.lower()) if transaction_type else None
            transaction = await TransactionCRUD.get_largest_in_period(session, user_id, start_date, end_date, tx_type)

            if not transaction:
                return None

            return TransactionInfo(
                id=transaction.id,
                type=transaction.type.value if hasattr(transaction.type, 'value') else str(transaction.type),
                amount=transaction.amount,
                currency=transaction.currency,
                account_from=transaction.account_from.name if transaction.account_from else None,
                account_to=transaction.account_to.name if transaction.account_to else None,
                description=transaction.description,
                date=transaction.date,
            )

    async def generate_monthly_report(self, input_data: QueryMonthlyReportInput, user_id: int) -> MonthlyReport:
        async with async_session_maker() as session:
            # Calculate date range for the month
            start_date = datetime(input_data.year, input_data.month, 1)
            if input_data.month == 12:
                end_date = datetime(input_data.year + 1, 1, 1)
            else:
                end_date = datetime(input_data.year, input_data.month + 1, 1)

            # Get totals
            total_income = await TransactionCRUD.get_total_by_type(
                session, user_id, start_date, end_date, TransactionType.INCOME
            )
            total_expenses = await TransactionCRUD.get_total_by_type(
                session, user_id, start_date, end_date, TransactionType.EXPENSE
            )

            # Get largest transaction
            largest_transaction = await self.get_largest_transaction(user_id, start_date, end_date)

            # Get current balances
            balances = await self.query_balances(QueryBalancesInput(), user_id)

            return MonthlyReport(
                month=input_data.month,
                year=input_data.year,
                total_income=total_income,
                total_expenses=total_expenses,
                net_savings=total_income - total_expenses,
                largest_transaction=largest_transaction,
                balances=balances,
            )

    async def generate_monthly_report_pdf(self, input_data: QueryMonthlyReportInput, user_id: int) -> str:
        """Generate a PDF version of the monthly report and return the file path."""
        # First get the regular monthly report
        report = await self.generate_monthly_report(input_data, user_id)

        # Get all transactions for the month
        from datetime import datetime
        start_date = datetime(input_data.year, input_data.month, 1)
        if input_data.month == 12:
            end_date = datetime(input_data.year + 1, 1, 1)
        else:
            end_date = datetime(input_data.year, input_data.month + 1, 1)

        transactions = await self.query_transactions(
            QueryTransactionsInput(
                start_date=start_date,
                end_date=end_date,
                account_name=None,
                transaction_type=None
            ), user_id
        )

        # Generate PDF
        # Create PDF service instance
        pdf_service = PDFReportService()

        pdf_data = pdf_service.generate_monthly_report_pdf(report, user_id, transactions)

        # Create temporary file
        filename = f"monthly_report_{input_data.year}_{input_data.month:02d}"
        return pdf_service.create_temp_pdf_file(pdf_data, filename)

    async def generate_transactions_pdf(self, input_data: QueryTransactionsInput, user_id: int) -> str:
        """Generate a PDF report with detailed transaction list and return the file path."""
        # Get all transactions for the period (no limit for PDF)
        transactions = await self.query_transactions(input_data, user_id)

        # Create PDF service instance
        pdf_service = PDFReportService()

        # Generate PDF
        pdf_data = pdf_service.generate_transactions_report_pdf(
            transactions,
            input_data.start_date,
            input_data.end_date,
            user_id,
            input_data.account_name
        )

        # Create temporary file
        start_str = input_data.start_date.strftime('%Y%m%d')
        end_str = input_data.end_date.strftime('%Y%m%d')
        filename = f"transactions_{start_str}_{end_str}"
        if input_data.account_name:
            filename += f"_{input_data.account_name.replace(' ', '_')}"

        return pdf_service.create_temp_pdf_file(pdf_data, filename)

    def _run(self, query: str) -> str:
        # This is a placeholder - actual implementation should parse the query
        # and route to the appropriate async method
        return "Use the async methods directly"

    async def _arun(self, query: str) -> str:
        return "Use specific methods like register_transaction, query_balances, etc."

    async def _handle_currency_conversion(self, session: AsyncSession, account_id: int,
                                        transaction_currency: str, transaction_amount: Decimal) -> tuple[str, Decimal, bool]:
        """
        Handle currency conversion when transaction currency differs from account currency.
        Returns the account currency, the converted amount, and whether conversion was successful.
        If conversion fails, returns None to indicate transaction should be queued.
        """
        # Get account's existing balances to determine primary currency
        account_balances = await session.execute(
            select(AccountBalance).where(AccountBalance.account_id == account_id)
        )
        balances = account_balances.scalars().all()

        if not balances:
            # No existing balance, use transaction currency
            return transaction_currency, transaction_amount, True

        # Find the balance with the highest amount (primary currency)
        primary_balance = max(balances, key=lambda b: b.balance)
        account_currency = primary_balance.currency

        if account_currency == transaction_currency:
            # Same currency, no conversion needed
            return account_currency, transaction_amount, True

        # Need to convert from transaction_currency to account_currency
        from src.agent.tools.fx_tool import FxTool
        fx_tool = FxTool()

        # Get exchange rate
        try:
            rate = await fx_tool.get_rate_value(transaction_currency, account_currency)
            if rate is None:
                # Try the reverse pair
                reverse_rate = await fx_tool.get_rate_value(account_currency, transaction_currency)
                if reverse_rate is None:
                    # Both failed - return failure to trigger pending transaction
                    return account_currency, transaction_amount, False
                rate = 1 / reverse_rate

            converted_amount = transaction_amount * Decimal(str(rate))
            return account_currency, converted_amount, True

        except Exception as e:
            # Exchange rate API failed - return failure to trigger pending transaction
            return account_currency, transaction_amount, False
