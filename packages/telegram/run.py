#!/usr/bin/env python3
"""
Entry point for the Telegram Bot.

This script starts the Telegram bot with proper path configuration.

Usage:
    python packages/telegram/run.py
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.telegram.bot import dp, bot, setup_bot_commands


async def start_bot():
    """Start the Telegram bot."""
    logger = logging.getLogger(__name__)

    try:
        # Set up bot commands
        await setup_bot_commands()
        logger.info("✅ Bot commands configured")

        # Start polling
        logger.info("🤖 Starting Telegram bot...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise
    finally:
        await bot.session.close()


async def main():
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info("🚀 Initializing Telegram Bot...")

    try:
        await start_bot()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
