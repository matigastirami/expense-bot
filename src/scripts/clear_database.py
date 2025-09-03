#!/usr/bin/env python3
"""
Clear all database records while keeping the schema intact.
This script will delete all data from tables but preserve the table structure.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.db.base import engine
from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def clear_all_records():
    """Clear all records from all tables in the correct order (respecting foreign keys)."""
    logger.info("Clearing all database records...")
    
    async with engine.begin() as conn:
        # Disable foreign key checks temporarily to avoid constraint issues
        await conn.execute(text("SET session_replication_role = replica;"))
        
        try:
            # Clear tables in reverse dependency order to avoid foreign key violations
            tables_to_clear = [
                "pending_transactions",
                "transactions", 
                "account_balances",
                "accounts",
                "exchange_rates",
                "users"
            ]
            
            for table in tables_to_clear:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count_before = result.scalar()
                
                if count_before > 0:
                    await conn.execute(text(f"DELETE FROM {table}"))
                    logger.info(f"  ✅ Cleared {count_before} records from {table}")
                else:
                    logger.info(f"  ℹ️  Table {table} was already empty")
                    
                # Reset auto-increment sequences
                await conn.execute(text(f"ALTER SEQUENCE IF EXISTS {table}_id_seq RESTART WITH 1"))
            
        finally:
            # Re-enable foreign key checks
            await conn.execute(text("SET session_replication_role = DEFAULT;"))
    
    logger.info("✅ All database records cleared successfully")


async def verify_empty_database():
    """Verify that all tables are empty."""
    logger.info("Verifying database is empty...")
    
    async with engine.begin() as conn:
        tables_to_check = [
            "users", "accounts", "account_balances", 
            "transactions", "pending_transactions", "exchange_rates"
        ]
        
        all_empty = True
        for table in tables_to_check:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            
            if count > 0:
                logger.warning(f"  ⚠️  Table {table} still has {count} records")
                all_empty = False
            else:
                logger.info(f"  ✅ Table {table} is empty")
        
        if all_empty:
            logger.info("🎉 Database is completely empty!")
        else:
            logger.error("❌ Some tables still have records")
            
        return all_empty


async def main():
    """Main entry point for clearing database records."""
    logger.info("🧹 Starting database cleanup...")
    logger.info(f"   Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    
    try:
        # Step 1: Clear all records
        await clear_all_records()
        
        # Step 2: Verify database is empty
        await verify_empty_database()
        
        logger.info("")
        logger.info("🎉 Database cleanup completed successfully!")
        logger.info("")
        logger.info("The database schema is preserved, but all data has been removed.")
        logger.info("You can now start fresh or run the reset script to add test data.")
        
    except Exception as e:
        logger.error(f"❌ Database cleanup failed: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())