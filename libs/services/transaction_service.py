"""Transaction service for transaction management operations."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.crud import TransactionCRUD, PendingTransactionCRUD
from libs.db.models import Transaction, TransactionType, PendingTransaction
from libs.validators import validate_transaction_data, validate_date_range
from libs.services.account_service import AccountService
from libs.integrations.fx.service import fx_service


class TransactionService:
    """Service for transaction-related operations."""

    @staticmethod
    async def create_transaction(
        session: AsyncSession,
        user_id: int,
        transaction_type: str,
        amount: float,
        currency: str,
        date: Optional[datetime] = None,
        account_from: Optional[str] = None,
        account_to: Optional[str] = None,
        currency_to: Optional[str] = None,
        amount_to: Optional[float] = None,
        exchange_rate: Optional[float] = None,
        description: Optional[str] = None,
    ) -> tuple[Optional[Transaction], Optional[str]]:
        """
        Create a new transaction with automatic balance updates.

        Args:
            session: Database session
            user_id: User ID
            transaction_type: Type of transaction (income, expense, transfer, conversion)
            amount: Transaction amount
            currency: Transaction currency
            date: Transaction date (default: now)
            account_from: Source account name
            account_to: Destination account name
            currency_to: Destination currency (for conversions/transfers)
            amount_to: Destination amount (for conversions/transfers with fees)
            exchange_rate: Exchange rate (for conversions)
            description: Transaction description

        Returns:
            Tuple of (transaction, error_message). If successful, transaction is not None and error is None.
        """
        # Validate transaction data
        is_valid, error = validate_transaction_data(
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            account_from=account_from,
            account_to=account_to,
            currency_to=currency_to,
            amount_to=amount_to,
            description=description,
            date=date,
        )
        if not is_valid:
            return None, error

        # Convert to proper types
        tx_type = TransactionType(transaction_type.lower())
        amount_decimal = Decimal(str(amount))
        amount_to_decimal = Decimal(str(amount_to)) if amount_to else None
        exchange_rate_decimal = Decimal(str(exchange_rate)) if exchange_rate else None
        # Use noon UTC for current date to avoid timezone boundary issues
        transaction_date = date or datetime.now(datetime.timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)

        # Get or create accounts
        account_from_obj = None
        account_to_obj = None

        if account_from:
            account_from_obj = await AccountService.get_or_create_account(
                session, user_id, account_from
            )

        if account_to:
            account_to_obj = await AccountService.get_or_create_account(
                session, user_id, account_to
            )

        # Process based on transaction type
        try:
            if tx_type == TransactionType.INCOME:
                return await TransactionService._process_income(
                    session, user_id, amount_decimal, currency,
                    account_to_obj, transaction_date, description
                )

            elif tx_type == TransactionType.EXPENSE:
                return await TransactionService._process_expense(
                    session, user_id, amount_decimal, currency,
                    account_from_obj, transaction_date, description
                )

            elif tx_type == TransactionType.TRANSFER:
                return await TransactionService._process_transfer(
                    session, user_id, amount_decimal, currency,
                    account_from_obj, account_to_obj,
                    currency_to, amount_to_decimal,
                    exchange_rate_decimal, transaction_date, description
                )

            elif tx_type == TransactionType.CONVERSION:
                return await TransactionService._process_conversion(
                    session, user_id, amount_decimal, currency,
                    account_from_obj, account_to_obj,
                    currency_to, amount_to_decimal,
                    exchange_rate_decimal, transaction_date, description
                )

        except Exception as e:
            await session.rollback()
            return None, f"Error processing transaction: {str(e)}"

    @staticmethod
    async def _process_income(
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        currency: str,
        account_to,
        date: datetime,
        description: Optional[str],
    ) -> tuple[Optional[Transaction], Optional[str]]:
        """Process income transaction."""
        # Handle currency conversion if needed
        account_currency, converted_amount, success = await TransactionService._handle_currency_conversion(
            session, user_id, account_to.id, currency, amount
        )

        if not success:
            # Queue as pending transaction
            await PendingTransactionCRUD.create(
                session=session,
                user_id=user_id,
                transaction_type=TransactionType.INCOME,
                currency=currency,
                amount=amount,
                date=date,
                account_to_id=account_to.id,
                description=description,
                last_error=f"Exchange rate unavailable for {currency}/{account_currency}",
            )
            return None, f"Transaction queued - Exchange rate for {currency}/{account_currency} temporarily unavailable"

        # Update balance if tracking is enabled
        if await AccountService.should_track_balance(session, user_id, account_to.id):
            await AccountService.add_to_account_balance(
                session, account_to.id, account_currency, converted_amount
            )

        # Create transaction
        transaction = await TransactionCRUD.create(
            session=session,
            user_id=user_id,
            transaction_type=TransactionType.INCOME,
            currency=currency,
            amount=amount,
            account_to_id=account_to.id,
            description=description,
            date=date,
        )

        return transaction, None

    @staticmethod
    async def _process_expense(
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        currency: str,
        account_from,
        date: datetime,
        description: Optional[str],
    ) -> tuple[Optional[Transaction], Optional[str]]:
        """Process expense transaction."""
        # Handle currency conversion if needed
        account_currency, converted_amount, success = await TransactionService._handle_currency_conversion(
            session, user_id, account_from.id, currency, amount
        )

        if not success:
            # Queue as pending transaction
            await PendingTransactionCRUD.create(
                session=session,
                user_id=user_id,
                transaction_type=TransactionType.EXPENSE,
                currency=currency,
                amount=amount,
                date=date,
                account_from_id=account_from.id,
                description=description,
                last_error=f"Exchange rate unavailable for {currency}/{account_currency}",
            )
            return None, f"Transaction queued - Exchange rate for {currency}/{account_currency} temporarily unavailable"

        # Update balance if tracking is enabled
        if await AccountService.should_track_balance(session, user_id, account_from.id):
            await AccountService.add_to_account_balance(
                session, account_from.id, account_currency, -converted_amount
            )

        # Create transaction
        transaction = await TransactionCRUD.create(
            session=session,
            user_id=user_id,
            transaction_type=TransactionType.EXPENSE,
            currency=currency,
            amount=amount,
            account_from_id=account_from.id,
            description=description,
            date=date,
        )

        return transaction, None

    @staticmethod
    async def _process_transfer(
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        currency: str,
        account_from,
        account_to,
        currency_to: Optional[str],
        amount_to: Optional[Decimal],
        exchange_rate: Optional[Decimal],
        date: datetime,
        description: Optional[str],
    ) -> tuple[Optional[Transaction], Optional[str]]:
        """Process transfer transaction."""
        # Determine destination currency and amount
        dest_currency = currency_to or currency
        dest_amount = amount_to or amount

        # Handle currency conversion for source account
        from_currency, from_converted_amount, from_success = await TransactionService._handle_currency_conversion(
            session, user_id, account_from.id, currency, amount
        )

        # Handle currency conversion for destination account
        to_currency, to_converted_amount, to_success = await TransactionService._handle_currency_conversion(
            session, user_id, account_to.id, dest_currency, dest_amount
        )

        if not from_success or not to_success:
            # Queue as pending transaction
            failed_pair = ""
            if not from_success:
                failed_pair += f"{currency}/{from_currency}"
            if not to_success:
                if failed_pair:
                    failed_pair += " and "
                failed_pair += f"{dest_currency}/{to_currency}"

            await PendingTransactionCRUD.create(
                session=session,
                user_id=user_id,
                transaction_type=TransactionType.TRANSFER,
                currency=currency,
                amount=amount,
                date=date,
                account_from_id=account_from.id,
                account_to_id=account_to.id,
                currency_to=dest_currency,
                amount_to=dest_amount,
                description=description,
                last_error=f"Exchange rate unavailable for {failed_pair}",
            )
            return None, f"Transaction queued - Exchange rate for {failed_pair} temporarily unavailable"

        # Update balances if tracking is enabled
        if await AccountService.should_track_balance(session, user_id, account_from.id):
            await AccountService.add_to_account_balance(
                session, account_from.id, from_currency, -from_converted_amount
            )

        if await AccountService.should_track_balance(session, user_id, account_to.id):
            await AccountService.add_to_account_balance(
                session, account_to.id, to_currency, to_converted_amount
            )

        # Create transaction
        transaction = await TransactionCRUD.create(
            session=session,
            user_id=user_id,
            transaction_type=TransactionType.TRANSFER,
            currency=currency,
            amount=amount,
            account_from_id=account_from.id,
            account_to_id=account_to.id,
            currency_to=dest_currency if dest_currency != currency else None,
            amount_to=dest_amount if dest_amount != amount else None,
            exchange_rate=exchange_rate,
            description=description,
            date=date,
        )

        return transaction, None

    @staticmethod
    async def _process_conversion(
        session: AsyncSession,
        user_id: int,
        amount: Decimal,
        currency: str,
        account_from,
        account_to,
        currency_to: str,
        amount_to: Decimal,
        exchange_rate: Optional[Decimal],
        date: datetime,
        description: Optional[str],
    ) -> tuple[Optional[Transaction], Optional[str]]:
        """Process conversion transaction."""
        # If no destination account specified, use same account as source
        if not account_to:
            account_to = account_from

        # Update balances if tracking is enabled
        if await AccountService.should_track_balance(session, user_id, account_from.id):
            # Remove source currency
            await AccountService.add_to_account_balance(
                session, account_from.id, currency, -amount
            )

        if await AccountService.should_track_balance(session, user_id, account_to.id):
            # Add destination currency
            await AccountService.add_to_account_balance(
                session, account_to.id, currency_to, amount_to
            )

        # Create transaction
        transaction = await TransactionCRUD.create(
            session=session,
            user_id=user_id,
            transaction_type=TransactionType.CONVERSION,
            currency=currency,
            amount=amount,
            account_from_id=account_from.id,
            account_to_id=account_to.id,
            currency_to=currency_to,
            amount_to=amount_to,
            exchange_rate=exchange_rate,
            description=description,
            date=date,
        )

        return transaction, None

    @staticmethod
    async def _handle_currency_conversion(
        session: AsyncSession,
        user_id: int,
        account_id: int,
        transaction_currency: str,
        transaction_amount: Decimal,
    ) -> tuple[str, Decimal, bool]:
        """
        Handle currency conversion when transaction currency differs from account currency.

        Returns:
            Tuple of (account_currency, converted_amount, success)
        """
        # Get account's primary currency (the one with the highest balance)
        from sqlalchemy import select
        from libs.db.models import AccountBalance

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
        try:
            rate, source = await fx_service.get_rate(transaction_currency, account_currency)
            if rate is None:
                # Try reverse pair
                reverse_rate, source = await fx_service.get_rate(account_currency, transaction_currency)
                if reverse_rate is None:
                    # Both failed - return failure
                    return account_currency, transaction_amount, False
                rate = Decimal("1") / reverse_rate

            converted_amount = transaction_amount * rate
            return account_currency, converted_amount, True

        except Exception as e:
            # Exchange rate API failed - return failure
            return account_currency, transaction_amount, False

    @staticmethod
    async def list_transactions(
        session: AsyncSession,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        account_name: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """
        List transactions for a user with filters.

        Args:
            session: Database session
            user_id: User ID
            start_date: Start date for filter
            end_date: End date for filter
            account_name: Optional account name filter
            transaction_type: Optional transaction type filter
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip

        Returns:
            Tuple of (transactions_list, error_message)
        """
        # Validate date range
        is_valid, error = validate_date_range(start_date, end_date)
        if not is_valid:
            return None, error

        # Get account ID if account name is provided
        account_id = None
        if account_name:
            account = await AccountService.get_account_by_name(session, user_id, account_name)
            if account:
                account_id = account.id

        # Get transactions
        transactions = await TransactionCRUD.get_by_date_range(
            session=session,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            limit=limit,
            offset=offset,
        )

        # Filter by type if specified
        if transaction_type:
            try:
                tx_type = TransactionType(transaction_type.lower())
                transactions = [t for t in transactions if t.type == tx_type]
            except ValueError:
                return None, f"Invalid transaction type: {transaction_type}"

        # Convert to dict format
        result = []
        for tx in transactions:
            result.append({
                "id": tx.id,
                "type": tx.type.value if hasattr(tx.type, 'value') else str(tx.type),
                "amount": float(tx.amount),
                "currency": tx.currency,
                "account_from": tx.account_from.name if tx.account_from else None,
                "account_to": tx.account_to.name if tx.account_to else None,
                "category_id": tx.category_id,
                "category": tx.category.name if tx.category else None,
                "merchant_id": tx.merchant_id,
                "merchant": tx.merchant.name if tx.merchant else None,
                "is_necessary": tx.is_necessary,
                "currency_to": tx.currency_to,
                "amount_to": float(tx.amount_to) if tx.amount_to else None,
                "exchange_rate": float(tx.exchange_rate) if tx.exchange_rate else None,
                "description": tx.description,
                "date": tx.date.isoformat(),
                "created_at": tx.created_at.isoformat(),
            })

        return result, None

    @staticmethod
    async def get_transaction_by_id(
        session: AsyncSession,
        user_id: int,
        transaction_id: int,
    ) -> Optional[Transaction]:
        """
        Get a specific transaction by ID.

        Args:
            session: Database session
            user_id: User ID
            transaction_id: Transaction ID

        Returns:
            Transaction if found and belongs to user, None otherwise
        """
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await session.execute(
            select(Transaction)
            .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
            .options(
                selectinload(Transaction.account_from),
                selectinload(Transaction.account_to),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_transaction(
        session: AsyncSession,
        user_id: int,
        transaction_id: int,
        amount: Optional[float] = None,
        description: Optional[str] = None,
        date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
        currency: Optional[str] = None,
        account_from: Optional[str] = None,
        account_to: Optional[str] = None,
        category_id: Optional[int] = None,
        merchant_id: Optional[int] = None,
        is_necessary: Optional[bool] = None,
        currency_to: Optional[str] = None,
        amount_to: Optional[float] = None,
        exchange_rate: Optional[float] = None,
    ) -> tuple[Optional[Transaction], Optional[str]]:
        """
        Update a transaction - all fields are editable.

        Args:
            session: Database session
            user_id: User ID
            transaction_id: Transaction ID
            amount: New amount (optional)
            description: New description (optional)
            date: New date (optional)
            transaction_type: New transaction type (optional)
            currency: New currency (optional)
            account_from: New source account name (optional)
            account_to: New destination account name (optional)
            category_id: New category ID (optional)
            merchant_id: New merchant ID (optional)
            is_necessary: New necessity flag (optional)
            currency_to: New destination currency (optional)
            amount_to: New destination amount (optional)
            exchange_rate: New exchange rate (optional)

        Returns:
            Tuple of (transaction, error_message)
        """
        # Get transaction
        transaction = await TransactionService.get_transaction_by_id(session, user_id, transaction_id)
        if not transaction:
            return None, "Transaction not found"

        # Update amount
        if amount is not None:
            if amount <= 0:
                return None, "Amount must be greater than 0"
            transaction.amount = Decimal(str(amount))

        # Update description
        if description is not None:
            if len(description) > 500:
                return None, "Description cannot exceed 500 characters"
            transaction.description = description

        # Update date
        if date is not None:
            transaction.date = date

        # Update transaction type
        if transaction_type is not None:
            try:
                tx_type = TransactionType(transaction_type.lower())
                transaction.type = tx_type
            except ValueError:
                return None, f"Invalid transaction type: {transaction_type}"

        # Update currency
        if currency is not None:
            transaction.currency = currency

        # Update account_from
        if account_from is not None:
            account_from_obj = await AccountService.get_or_create_account(
                session, user_id, account_from
            )
            transaction.account_from_id = account_from_obj.id

        # Update account_to
        if account_to is not None:
            account_to_obj = await AccountService.get_or_create_account(
                session, user_id, account_to
            )
            transaction.account_to_id = account_to_obj.id

        # Update category_id
        if category_id is not None:
            transaction.category_id = category_id

        # Update merchant_id
        if merchant_id is not None:
            transaction.merchant_id = merchant_id

        # Update is_necessary
        if is_necessary is not None:
            transaction.is_necessary = is_necessary

        # Update currency_to
        if currency_to is not None:
            transaction.currency_to = currency_to

        # Update amount_to
        if amount_to is not None:
            if amount_to <= 0:
                return None, "Amount to must be greater than 0"
            transaction.amount_to = Decimal(str(amount_to))

        # Update exchange_rate
        if exchange_rate is not None:
            if exchange_rate <= 0:
                return None, "Exchange rate must be greater than 0"
            transaction.exchange_rate = Decimal(str(exchange_rate))

        await session.commit()

        # Eagerly load relationships to avoid lazy loading issues
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await session.execute(
            select(Transaction)
            .where(Transaction.id == transaction.id)
            .options(
                selectinload(Transaction.account_from),
                selectinload(Transaction.account_to),
                selectinload(Transaction.category),
                selectinload(Transaction.merchant),
            )
        )
        transaction = result.scalar_one()

        return transaction, None
