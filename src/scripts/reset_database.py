#!/usr/bin/env python3
"""
Database reset and seed script for the expense tracker.
This script will drop all tables and recreate them with fresh schema.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from libs.db.base import engine, async_session_maker
from libs.db.models import Base
from libs.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def drop_all_tables():
    """Drop all tables in the database."""
    logger.info("Dropping all tables...")

    async with engine.begin() as conn:
        # Drop all tables in the correct order (reverse dependency)
        await conn.execute(text("DROP TABLE IF EXISTS pending_transactions CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS account_balances CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS accounts CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS exchange_rates CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))

        # Drop the alembic version table to start fresh
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))

        # Drop enums if they exist
        await conn.execute(text("DROP TYPE IF EXISTS transactiontype CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS accounttype CASCADE"))

    logger.info("✅ All tables dropped successfully")


async def create_all_tables():
    """Create all tables using SQLAlchemy models."""
    logger.info("Creating all tables...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ All tables created successfully")


async def seed_test_data():
    """Seed the database with test data."""
    logger.info("Seeding test data...")

    from libs.db.crud import AccountCRUD, AccountBalanceCRUD, TransactionCRUD
    from libs.db.models import User, AccountType, TransactionType
    from decimal import Decimal
    from datetime import datetime, timezone

    async with async_session_maker() as session:
        # Create a test user
        test_user = User(
            telegram_user_id="123456789",
            first_name="Test",
            last_name="User",
            username="testuser",
            language_code="es"
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)

        # Create test accounts
        accounts_data = [
            ("Deel", AccountType.WALLET),
            ("Astropay", AccountType.WALLET),
            ("Galicia", AccountType.BANK),
            ("Efectivo", AccountType.CASH),
        ]

        accounts = {}
        for name, account_type in accounts_data:
            account = await AccountCRUD.create(session, test_user.id, name, account_type)
            accounts[name] = account

        # Add initial balances
        balances_data = [
            ("Deel", "USD", Decimal("5000.00")),
            ("Astropay", "USD", Decimal("1000.00")),
            ("Galicia", "ARS", Decimal("250000.00")),
            ("Efectivo", "ARS", Decimal("50000.00")),
        ]

        for account_name, currency, balance in balances_data:
            account = accounts[account_name]
            await AccountBalanceCRUD.add_to_balance(session, account.id, currency, balance)

        # Add some test transactions
        transactions_data = [
            {
                "transaction_type": TransactionType.INCOME,
                "amount": Decimal("5000.00"),
                "currency": "USD",
                "account_to_id": accounts["Deel"].id,
                "description": "Salary payment",
                "date": datetime.now(timezone.utc)
            },
            {
                "transaction_type": TransactionType.EXPENSE,
                "amount": Decimal("50000.00"),
                "currency": "ARS",
                "account_from_id": accounts["Galicia"].id,
                "description": "Supermercado",
                "date": datetime.now(timezone.utc)
            },
            {
                "transaction_type": TransactionType.TRANSFER,
                "amount": Decimal("500.00"),
                "currency": "USD",
                "account_from_id": accounts["Deel"].id,
                "account_to_id": accounts["Astropay"].id,
                "description": "Transfer to Astropay",
                "date": datetime.now(timezone.utc)
            },
        ]

        for tx_data in transactions_data:
            await TransactionCRUD.create(
                session=session,
                user_id=test_user.id,
                **tx_data
            )

    logger.info("✅ Test data seeded successfully")
    logger.info(f"   📧 Test user: telegram_user_id=123456789")
    logger.info(f"   💰 Accounts created: Deel (5000 USD), Astropay (1000 USD), Galicia (250000 ARS), Efectivo (50000 ARS)")
    logger.info(f"   📊 Sample transactions added")


async def reset_alembic():
    """Initialize alembic with the current schema."""
    logger.info("Initializing Alembic...")

    async with engine.begin() as conn:
        # Create alembic_version table and mark as current
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """))

        # Insert the latest version (this should match your latest migration)
        await conn.execute(text("""
            INSERT INTO alembic_version (version_num)
            VALUES ('2e5aa12f0766')
            ON CONFLICT (version_num) DO NOTHING
        """))

    logger.info("✅ Alembic initialized successfully")


async def main():
    """Main entry point for the database reset."""
    logger.info("🔄 Starting database reset...")
    logger.info(f"   Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")

    try:
        # Step 1: Drop all tables
        await drop_all_tables()

        # Step 2: Create all tables
        await create_all_tables()

        # Step 3: Reset Alembic
        await reset_alembic()

        # Step 4: Seed test data
        await seed_test_data()

        logger.info("🎉 Database reset completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Start the Telegram bot: docker-compose up")
        logger.info("2. Test with telegram_user_id: 123456789")
        logger.info("3. Or create new users by talking to the bot")

    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
