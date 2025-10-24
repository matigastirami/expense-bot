"""Validators for user-related data."""

import re
from typing import Optional


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"

    email = email.strip().lower()

    # Basic email regex pattern
    email_pattern = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,}$'

    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    if len(email) > 255:
        return False, "Email address too long (max 255 characters)"

    return True, None


def validate_password(password: str, min_length: int = 8) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.

    Args:
        password: Password to validate
        min_length: Minimum password length (default: 8)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"

    if len(password) > 128:
        return False, "Password too long (max 128 characters)"

    # Check for at least one letter
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"

    # Check for at least one number
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    return True, None


def validate_telegram_user_id(telegram_user_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate Telegram user ID format.

    Args:
        telegram_user_id: Telegram user ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not telegram_user_id:
        return False, "Telegram user ID is required"

    if not telegram_user_id.isdigit():
        return False, "Telegram user ID must be numeric"

    if len(telegram_user_id) > 50:
        return False, "Telegram user ID too long"

    return True, None


def validate_language_code(language_code: str) -> tuple[bool, Optional[str]]:
    """
    Validate language code format.

    Args:
        language_code: Language code to validate (e.g., 'en', 'es')

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not language_code:
        return True, None  # Language code is optional

    # Should be 2-5 characters (e.g., 'en', 'es', 'en-US')
    if len(language_code) < 2 or len(language_code) > 10:
        return False, "Language code must be 2-10 characters"

    if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', language_code):
        return False, "Invalid language code format (expected: 'en' or 'en-US')"

    return True, None
