"""
Bot integration module for Financial Analysis Agent.

This module automatically registers the financial agent handlers with the main bot
when imported. It provides seamless integration with the existing bot infrastructure.
"""

import logging
from aiogram import Dispatcher

from packages.telegram.financial_agent_handlers import financial_router

logger = logging.getLogger(__name__)


def register_financial_agent_handlers(dp: Dispatcher) -> None:
    """
    Register financial agent handlers with the main dispatcher.

    Args:
        dp: Main Telegram bot dispatcher
    """
    try:
        # Include the financial router
        dp.include_router(financial_router)
        logger.info("✅ Financial Analysis Agent handlers registered successfully")

    except Exception as e:
        logger.error(f"❌ Failed to register Financial Analysis Agent handlers: {e}")
        raise


# Auto-registration when module is imported
# This ensures the handlers are registered when the bot starts
try:
    # Import the main dispatcher from the bot module
    from packages.telegram.bot import dp
    register_financial_agent_handlers(dp)

except ImportError:
    # If main bot module isn't available yet, handlers will be registered manually
    logger.warning("Main bot dispatcher not available during import. Handlers will need to be registered manually.")
except Exception as e:
    logger.error(f"Error during auto-registration: {e}")


# Export the router for manual registration if needed
__all__ = ["financial_router", "register_financial_agent_handlers"]
