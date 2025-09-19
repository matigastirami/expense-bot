"""Keyboard builders for the Telegram bot interface."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

from src.db.models import BalanceTrackingMode


def build_main_settings_keyboard(user_balance_mode: str) -> InlineKeyboardMarkup:
    """Build the main settings menu keyboard."""

    balance_mode_display = "🔧 STRICT" if user_balance_mode == BalanceTrackingMode.STRICT else "📝 LOGGING"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"💰 Balance Tracking: {balance_mode_display}",
            callback_data="settings_balance"
        )],
        [InlineKeyboardButton(
            text="🏦 Account Settings",
            callback_data="settings_accounts"
        )],
        [InlineKeyboardButton(
            text="❌ Close Settings",
            callback_data="settings_close"
        )]
    ])


def build_balance_settings_keyboard(current_mode: str) -> InlineKeyboardMarkup:
    """Build the balance tracking settings keyboard."""

    if current_mode == BalanceTrackingMode.STRICT:
        # Currently in STRICT mode
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔧 STRICT Mode ✅",
                callback_data="balance_mode_info_strict"
            )],
            [InlineKeyboardButton(
                text="• Prevents negative balances",
                callback_data="noop"
            )],
            [InlineKeyboardButton(
                text="• Enforces account limits",
                callback_data="noop"
            )],
            [InlineKeyboardButton(
                text="• Provides balance warnings",
                callback_data="noop"
            )],
            [InlineKeyboardButton(
                text="🔄 Switch to LOGGING Mode",
                callback_data="balance_change_logging"
            )],
            [InlineKeyboardButton(
                text="⬅️ Back to Settings",
                callback_data="settings_main"
            )]
        ])
    else:
        # Currently in LOGGING mode
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📝 LOGGING Mode ✅",
                callback_data="balance_mode_info_logging"
            )],
            [InlineKeyboardButton(
                text="• Allows any transaction amount",
                callback_data="noop"
            )],
            [InlineKeyboardButton(
                text="• Focuses on transaction recording",
                callback_data="noop"
            )],
            [InlineKeyboardButton(
                text="• No balance constraints",
                callback_data="noop"
            )],
            [InlineKeyboardButton(
                text="🔄 Switch to STRICT Mode",
                callback_data="balance_change_strict"
            )],
            [InlineKeyboardButton(
                text="⬅️ Back to Settings",
                callback_data="settings_main"
            )]
        ])


def build_confirmation_keyboard(new_mode: str) -> InlineKeyboardMarkup:
    """Build confirmation keyboard for balance mode changes."""

    mode_name = "STRICT" if new_mode == BalanceTrackingMode.STRICT else "LOGGING"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"✅ Yes, switch to {mode_name}",
            callback_data=f"confirm_balance_{new_mode}"
        )],
        [InlineKeyboardButton(
            text="❌ Cancel",
            callback_data="settings_balance"
        )]
    ])


def build_account_settings_keyboard(accounts: List[dict]) -> InlineKeyboardMarkup:
    """Build keyboard for per-account settings."""

    buttons = []

    # Add account rows
    for account in accounts[:5]:  # Limit to 5 accounts for display
        track_status = "🔧" if account.get('track_balance') is True else "📝" if account.get('track_balance') is False else "⚙️"
        buttons.append([InlineKeyboardButton(
            text=f"{track_status} {account['name']}",
            callback_data=f"account_toggle_{account['id']}"
        )])

    # Add navigation buttons
    if len(accounts) > 5:
        buttons.append([InlineKeyboardButton(
            text="➡️ Show More Accounts",
            callback_data="accounts_page_2"
        )])

    buttons.append([InlineKeyboardButton(
        text="⬅️ Back to Settings",
        callback_data="settings_main"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
