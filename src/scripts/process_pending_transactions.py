#!/usr/bin/env python3
"""
Process pending transactions by retrying exchange rate fetching.
This script runs every 2 hours to process transactions that failed due to exchange rate unavailability.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import List

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.agent.tools.fx_tool import FxTool
from libs.db.base import async_session_maker
from libs.db.crud import AccountBalanceCRUD, PendingTransactionCRUD, TransactionCRUD
from libs.db.models import PendingTransaction, TransactionType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PendingTransactionProcessor:
    def __init__(self):
        self.fx_tool = FxTool()
        self.max_retries = 10  # Stop after 10 failed attempts

    async def process_all_pending(self) -> None:
        """Process all pending transactions with low retry count."""
        async with async_session_maker() as session:
            pending_transactions = await PendingTransactionCRUD.get_pending_with_low_retry_count(
                session, self.max_retries
            )

            if not pending_transactions:
                logger.info("No pending transactions to process")
                return

            logger.info(f"Processing {len(pending_transactions)} pending transactions")

            processed_count = 0
            for pending_tx in pending_transactions:
                try:
                    success = await self._process_single_transaction(session, pending_tx)
                    if success:
                        processed_count += 1
                        logger.info(f"Successfully processed pending transaction {pending_tx.id}")
                    else:
                        logger.warning(f"Failed to process pending transaction {pending_tx.id}")
                except Exception as e:
                    logger.error(f"Error processing pending transaction {pending_tx.id}: {e}")
                    await PendingTransactionCRUD.update_retry_info(
                        session, pending_tx.id, pending_tx.retry_count + 1, str(e)
                    )

            logger.info(f"Successfully processed {processed_count}/{len(pending_transactions)} transactions")

    async def _process_single_transaction(self, session, pending_tx: PendingTransaction) -> bool:
        """Process a single pending transaction."""
        try:
            transaction_type = TransactionType(pending_tx.transaction_type)

            # Try to get exchange rate
            if transaction_type in [TransactionType.INCOME, TransactionType.EXPENSE]:
                success = await self._handle_simple_transaction(session, pending_tx, transaction_type)
            elif transaction_type == TransactionType.TRANSFER:
                success = await self._handle_transfer_transaction(session, pending_tx)
            elif transaction_type == TransactionType.CONVERSION:
                success = await self._handle_conversion_transaction(session, pending_tx)
            else:
                logger.error(f"Unknown transaction type: {transaction_type}")
                return False

            if success:
                # Delete the pending transaction
                await PendingTransactionCRUD.delete(session, pending_tx.id)
                return True
            else:
                # Increment retry count
                await PendingTransactionCRUD.update_retry_info(
                    session, pending_tx.id, pending_tx.retry_count + 1,
                    "Exchange rate still unavailable"
                )
                return False

        except Exception as e:
            await PendingTransactionCRUD.update_retry_info(
                session, pending_tx.id, pending_tx.retry_count + 1, str(e)
            )
            return False

    async def _handle_simple_transaction(self, session, pending_tx: PendingTransaction,
                                       transaction_type: TransactionType) -> bool:
        """Handle income or expense transactions."""
        account_id = pending_tx.account_to_id if transaction_type == TransactionType.INCOME else pending_tx.account_from_id
        if not account_id:
            return False

        # Get account currency and try conversion
        account_currency, converted_amount, success = await self._get_converted_amount(
            session, account_id, pending_tx.currency, pending_tx.amount
        )

        if not success:
            return False

        # Apply the balance change
        multiplier = 1 if transaction_type == TransactionType.INCOME else -1
        await AccountBalanceCRUD.add_to_balance(
            session, account_id, account_currency, multiplier * converted_amount
        )

        # Create the actual transaction record
        await TransactionCRUD.create(
            session=session,
            transaction_type=transaction_type,
            currency=pending_tx.currency,
            amount=pending_tx.amount,
            account_from_id=pending_tx.account_from_id,
            account_to_id=pending_tx.account_to_id,
            description=pending_tx.description,
            date=pending_tx.date,
        )

        return True

    async def _handle_transfer_transaction(self, session, pending_tx: PendingTransaction) -> bool:
        """Handle transfer transactions."""
        if not pending_tx.account_from_id or not pending_tx.account_to_id:
            return False

        # Handle source conversion
        from_currency, from_converted_amount, from_success = await self._get_converted_amount(
            session, pending_tx.account_from_id, pending_tx.currency, pending_tx.amount
        )

        # Handle destination conversion
        destination_amount = pending_tx.amount_to or pending_tx.amount
        destination_currency = pending_tx.currency_to or pending_tx.currency

        to_currency, to_converted_amount, to_success = await self._get_converted_amount(
            session, pending_tx.account_to_id, destination_currency, destination_amount
        )

        if not from_success or not to_success:
            return False

        # Apply balance changes
        await AccountBalanceCRUD.add_to_balance(
            session, pending_tx.account_from_id, from_currency, -from_converted_amount
        )
        await AccountBalanceCRUD.add_to_balance(
            session, pending_tx.account_to_id, to_currency, to_converted_amount
        )

        # Create the actual transaction record
        await TransactionCRUD.create(
            session=session,
            transaction_type=TransactionType.TRANSFER,
            currency=pending_tx.currency,
            amount=pending_tx.amount,
            account_from_id=pending_tx.account_from_id,
            account_to_id=pending_tx.account_to_id,
            currency_to=pending_tx.currency_to,
            amount_to=pending_tx.amount_to,
            exchange_rate=pending_tx.exchange_rate,
            description=pending_tx.description,
            date=pending_tx.date,
        )

        return True

    async def _handle_conversion_transaction(self, session, pending_tx: PendingTransaction) -> bool:
        """Handle conversion transactions."""
        if not pending_tx.account_from_id or not pending_tx.currency_to or not pending_tx.amount_to:
            return False

        account_to_id = pending_tx.account_to_id or pending_tx.account_from_id

        # Try to get the exchange rate
        try:
            rate = await self.fx_tool.get_rate_value(pending_tx.currency, pending_tx.currency_to)
            if rate is None:
                # Try reverse pair
                reverse_rate = await self.fx_tool.get_rate_value(pending_tx.currency_to, pending_tx.currency)
                if reverse_rate is None:
                    return False
                rate = 1 / reverse_rate
        except Exception:
            return False

        # Apply balance changes
        await AccountBalanceCRUD.add_to_balance(
            session, pending_tx.account_from_id, pending_tx.currency, -pending_tx.amount
        )
        await AccountBalanceCRUD.add_to_balance(
            session, account_to_id, pending_tx.currency_to, pending_tx.amount_to
        )

        # Create the actual transaction record
        await TransactionCRUD.create(
            session=session,
            transaction_type=TransactionType.CONVERSION,
            currency=pending_tx.currency,
            amount=pending_tx.amount,
            account_from_id=pending_tx.account_from_id,
            account_to_id=account_to_id,
            currency_to=pending_tx.currency_to,
            amount_to=pending_tx.amount_to,
            exchange_rate=Decimal(str(rate)),
            description=pending_tx.description,
            date=pending_tx.date,
        )

        return True

    async def _get_converted_amount(self, session, account_id: int,
                                  transaction_currency: str, transaction_amount: Decimal) -> tuple[str, Decimal, bool]:
        """Get converted amount for an account, similar to db_tool logic."""
        # Get account's existing balances to determine primary currency
        from sqlalchemy import select
        from libs.db.models import AccountBalance

        account_balances = await session.execute(
            select(AccountBalance).where(AccountBalance.account_id == account_id)
        )
        balances = account_balances.scalars().all()

        if not balances:
            return transaction_currency, transaction_amount, True

        # Find primary currency (highest balance)
        primary_balance = max(balances, key=lambda b: b.balance)
        account_currency = primary_balance.currency

        if account_currency == transaction_currency:
            return account_currency, transaction_amount, True

        # Try to get exchange rate
        try:
            rate = await self.fx_tool.get_rate_value(transaction_currency, account_currency)
            if rate is None:
                # Try reverse pair
                reverse_rate = await self.fx_tool.get_rate_value(account_currency, transaction_currency)
                if reverse_rate is None:
                    return account_currency, transaction_amount, False
                rate = 1 / reverse_rate

            converted_amount = transaction_amount * Decimal(str(rate))
            return account_currency, converted_amount, True

        except Exception:
            return account_currency, transaction_amount, False


async def main():
    """Main entry point for the cron job."""
    logger.info("Starting pending transaction processor")

    processor = PendingTransactionProcessor()

    try:
        await processor.process_all_pending()
        logger.info("Pending transaction processing completed successfully")
    except Exception as e:
        logger.error(f"Error in pending transaction processor: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
