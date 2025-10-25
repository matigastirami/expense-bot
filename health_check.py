#!/usr/bin/env python3
"""
Health check script to verify all imports work correctly.
Run this before starting the application.
"""

import sys
import os

def check_imports():
    """Check if all core imports work."""
    try:
        print("🔍 Checking core imports...")

        # Basic imports
        print("  ✓ Checking config...")
        from libs.config import settings

        print("  ✓ Checking database models...")
        from libs.db.models import Account, AccountBalance, Transaction, ExchangeRate
        from libs.db.base import Base, engine

        print("  ✓ Checking CRUD operations...")
        from libs.db.crud import AccountCRUD, TransactionCRUD

        print("  ✓ Checking agent schemas...")
        from packages.agent.schemas import ParsedTransactionIntent, ParsedQueryIntent

        print("  ✓ Checking FX providers...")
        from libs.integrations.fx.providers.coingecko import CoinGeckoProvider
        from libs.integrations.fx.providers.ars_sources import ARSProvider
        from libs.integrations.fx.service import fx_service

        print("  ✓ Checking agent tools...")
        from packages.agent.tools.db_tool import DbTool
        from packages.agent.tools.fx_tool import FxTool

        print("  ✓ Checking agent...")
        from packages.agent.agent import FinanceAgent

        print("  ✓ Checking Telegram bot...")
        from packages.telegram.bot import dp, bot

        print("✅ All imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_environment():
    """Check environment variables."""
    print("🔍 Checking environment variables...")

    required_vars = [
        "OPENAI_API_KEY",
        "TELEGRAM_BOT_TOKEN"
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        return False

    print("✅ Environment variables OK!")
    return True


def check_file_structure():
    """Check that required files exist."""
    print("🔍 Checking file structure...")

    required_files = [
        "src/agent/prompts/system.md",
        "src/agent/prompts/fewshots.md",
        ".env.example"
    ]

    missing = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing.append(file_path)

    if missing:
        print(f"❌ Missing required files: {', '.join(missing)}")
        return False

    print("✅ File structure OK!")
    return True


async def check_database_connection():
    """Check database connectivity."""
    try:
        print("🔍 Checking database connection...")
        from libs.db.base import engine

        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            result.fetchone()

        print("✅ Database connection OK!")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def main():
    """Run all health checks."""
    print("🏥 Starting health check...\n")

    checks = [
        ("Environment", check_environment()),
        ("File Structure", check_file_structure()),
        ("Imports", check_imports()),
    ]

    # Database check is async
    db_check = await check_database_connection()
    checks.append(("Database", db_check))

    print("\n📊 Health Check Results:")
    print("-" * 30)

    all_passed = True
    for name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:15}: {status}")
        if not passed:
            all_passed = False

    print("-" * 30)

    if all_passed:
        print("🎉 All checks passed! Application is ready to start.")
        return 0
    else:
        print("🚨 Some checks failed! Please fix issues before starting.")
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
