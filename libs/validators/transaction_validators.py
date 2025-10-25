"""Validators for transaction-related data."""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any
from datetime import datetime

from libs.db.models import TransactionType


# Common currency codes
VALID_CURRENCIES = {
    "USD", "EUR", "GBP", "JPY", "CNY", "AUD", "CAD", "CHF", "SEK", "NZD",
    "ARS", "BRL", "MXN", "COP", "CLP", "PEN", "UYU",  # Latin American currencies
    "USDT", "USDC", "DAI", "BTC", "ETH",  # Cryptocurrencies
}


def validate_currency(currency: str) -> tuple[bool, Optional[str]]:
    """
    Validate currency code.

    Args:
        currency: Currency code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not currency:
        return False, "Currency is required"

    currency = currency.upper().strip()

    if len(currency) < 2 or len(currency) > 10:
        return False, "Currency code must be between 2 and 10 characters"

    if not re.match(r'^[A-Z0-9]+$', currency):
        return False, "Currency code must contain only uppercase letters and numbers"

    # Warn if currency is not in the common list (but still allow it)
    if currency not in VALID_CURRENCIES:
        # This is a warning, not an error - we still allow uncommon currencies
        pass

    return True, None


def validate_amount(amount: Any, min_value: Optional[Decimal] = None) -> tuple[bool, Optional[str]]:
    """
    Validate transaction amount.

    Args:
        amount: Amount to validate (can be str, float, int, or Decimal)
        min_value: Minimum allowed value (default: 0)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if amount is None:
        return False, "Amount is required"

    try:
        # Convert to Decimal for precise validation
        if isinstance(amount, str):
            amount_decimal = Decimal(amount)
        elif isinstance(amount, (int, float)):
            amount_decimal = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            amount_decimal = amount
        else:
            return False, f"Invalid amount type: {type(amount).__name__}"
    except (InvalidOperation, ValueError):
        return False, f"Invalid amount format: {amount}"

    # Check minimum value
    min_val = min_value if min_value is not None else Decimal("0")
    if amount_decimal <= min_val:
        return False, f"Amount must be greater than {min_val}"

    # Check for reasonable precision (max 8 decimal places)
    if amount_decimal.as_tuple().exponent < -8:
        return False, "Amount cannot have more than 8 decimal places"

    return True, None


def validate_transaction_type(transaction_type: str) -> tuple[bool, Optional[str]]:
    """
    Validate transaction type.

    Args:
        transaction_type: Transaction type to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not transaction_type:
        return False, "Transaction type is required"

    try:
        # Try to convert to TransactionType enum
        TransactionType(transaction_type.lower())
        return True, None
    except ValueError:
        valid_types = [t.value for t in TransactionType]
        return False, f"Invalid transaction type. Must be one of: {', '.join(valid_types)}"


def validate_transaction_data(
    transaction_type: str,
    amount: Any,
    currency: str,
    account_from: Optional[str] = None,
    account_to: Optional[str] = None,
    currency_to: Optional[str] = None,
    amount_to: Optional[Any] = None,
    description: Optional[str] = None,
    date: Optional[datetime] = None,
) -> tuple[bool, Optional[str]]:
    """
    Validate complete transaction data based on transaction type.

    Args:
        transaction_type: Type of transaction
        amount: Transaction amount
        currency: Transaction currency
        account_from: Source account name
        account_to: Destination account name
        currency_to: Destination currency (for conversions)
        amount_to: Destination amount (for conversions/transfers)
        description: Transaction description
        date: Transaction date

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate transaction type
    is_valid, error = validate_transaction_type(transaction_type)
    if not is_valid:
        return False, error

    tx_type = TransactionType(transaction_type.lower())

    # Validate amount
    is_valid, error = validate_amount(amount)
    if not is_valid:
        return False, error

    # Validate currency
    is_valid, error = validate_currency(currency)
    if not is_valid:
        return False, error

    # Validate description length
    if description and len(description) > 500:
        return False, "Description cannot exceed 500 characters"

    # Type-specific validations
    if tx_type == TransactionType.INCOME:
        if not account_to:
            return False, "Income transactions require a destination account (account_to)"
        if account_from:
            return False, "Income transactions should not have a source account"

    elif tx_type == TransactionType.EXPENSE:
        if not account_from:
            return False, "Expense transactions require a source account (account_from)"
        if account_to:
            return False, "Expense transactions should not have a destination account"

    elif tx_type == TransactionType.TRANSFER:
        if not account_from or not account_to:
            return False, "Transfer transactions require both source and destination accounts"
        if account_from == account_to:
            return False, "Source and destination accounts must be different for transfers"

        # Validate amount_to if provided
        if amount_to is not None:
            is_valid, error = validate_amount(amount_to)
            if not is_valid:
                return False, f"Invalid destination amount: {error}"

        # Validate currency_to if provided
        if currency_to:
            is_valid, error = validate_currency(currency_to)
            if not is_valid:
                return False, f"Invalid destination currency: {error}"

    elif tx_type == TransactionType.CONVERSION:
        if not account_from:
            return False, "Conversion transactions require a source account (account_from)"
        if not currency_to:
            return False, "Conversion transactions require a destination currency (currency_to)"
        if not amount_to:
            return False, "Conversion transactions require a destination amount (amount_to)"

        # Validate amount_to
        is_valid, error = validate_amount(amount_to)
        if not is_valid:
            return False, f"Invalid destination amount: {error}"

        # Validate currency_to
        is_valid, error = validate_currency(currency_to)
        if not is_valid:
            return False, f"Invalid destination currency: {error}"

        if currency == currency_to:
            return False, "Source and destination currencies must be different for conversions"

    return True, None


def validate_date_range(start_date: datetime, end_date: datetime) -> tuple[bool, Optional[str]]:
    """
    Validate date range for queries.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not start_date:
        return False, "Start date is required"

    if not end_date:
        return False, "End date is required"

    if start_date > end_date:
        return False, "Start date must be before or equal to end date"

    # Check if date range is reasonable (not more than 10 years)
    if (end_date - start_date).days > 3650:
        return False, "Date range cannot exceed 10 years"

    return True, None
