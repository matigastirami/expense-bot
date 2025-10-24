"""Validators for account-related data."""

from typing import Optional

from libs.db.models import AccountType


def validate_account_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Validate account name.

    Args:
        name: Account name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Account name is required"

    name = name.strip()

    if len(name) < 1:
        return False, "Account name cannot be empty"

    if len(name) > 255:
        return False, "Account name too long (max 255 characters)"

    # Check for invalid characters (allow letters, numbers, spaces, and common punctuation)
    if not all(c.isalnum() or c.isspace() or c in "'-_()&." for c in name):
        return False, "Account name contains invalid characters"

    return True, None


def validate_account_type(account_type: str) -> tuple[bool, Optional[str]]:
    """
    Validate account type.

    Args:
        account_type: Account type to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not account_type:
        return False, "Account type is required"

    try:
        # Try to convert to AccountType enum
        AccountType(account_type.lower())
        return True, None
    except ValueError:
        valid_types = [t.value for t in AccountType]
        return False, f"Invalid account type. Must be one of: {', '.join(valid_types)}"
