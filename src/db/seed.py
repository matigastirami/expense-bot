"""
Database seeding script for development and testing.
Creates sample accounts, transactions, and exchange rates.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from src.db.base import async_session_maker
from src.db.crud import AccountCRUD, ExchangeRateCRUD, TransactionCRUD
from src.db.models import AccountType, TransactionType


async def seed_database():
    """Seed database with sample data."""
    async with async_session_maker() as session:
        print("🌱 Seeding database with sample data...")
        
        # Create sample accounts
        deel_account = await AccountCRUD.create(session, "Deel", AccountType.BANK)
        astropay_account = await AccountCRUD.create(session, "Astropay", AccountType.WALLET)
        galicia_account = await AccountCRUD.create(session, "Galicia", AccountType.BANK)
        belo_account = await AccountCRUD.create(session, "Belo", AccountType.WALLET)
        cash_account = await AccountCRUD.create(session, "Cash", AccountType.CASH)
        
        print(f"✅ Created {5} sample accounts")
        
        # Create sample transactions
        now = datetime.utcnow()
        
        transactions = [
            # Income transactions
            {
                "type": TransactionType.INCOME,
                "account_to_id": deel_account.id,
                "currency": "USD",
                "amount": Decimal("6000.00"),
                "description": "August salary",
                "date": now - timedelta(days=5)
            },
            {
                "type": TransactionType.INCOME,
                "account_to_id": deel_account.id,
                "currency": "USD", 
                "amount": Decimal("2500.00"),
                "description": "Freelance project",
                "date": now - timedelta(days=3)
            },
            
            # Expense transactions
            {
                "type": TransactionType.EXPENSE,
                "account_from_id": cash_account.id,
                "currency": "ARS",
                "amount": Decimal("45000.00"),
                "description": "Groceries",
                "date": now - timedelta(days=2)
            },
            {
                "type": TransactionType.EXPENSE,
                "account_from_id": galicia_account.id,
                "currency": "ARS",
                "amount": Decimal("120000.00"),
                "description": "Rent payment",
                "date": now - timedelta(days=1)
            },
            
            # Transfer transaction
            {
                "type": TransactionType.TRANSFER,
                "account_from_id": deel_account.id,
                "account_to_id": astropay_account.id,
                "currency": "USD",
                "amount": Decimal("1000.00"),
                "currency_to": "USD",
                "amount_to": Decimal("992.00"),
                "description": "Transfer with fees",
                "date": now - timedelta(hours=12)
            },
            
            # Conversion transaction
            {
                "type": TransactionType.CONVERSION,
                "account_from_id": belo_account.id,
                "account_to_id": belo_account.id,
                "currency": "USDT",
                "amount": Decimal("100.00"),
                "currency_to": "ARS",
                "amount_to": Decimal("135000.00"),
                "exchange_rate": Decimal("1350.00"),
                "description": "USDT to ARS conversion",
                "date": now - timedelta(hours=6)
            }
        ]
        
        for tx_data in transactions:
            await TransactionCRUD.create(session, **tx_data)
        
        print(f"✅ Created {len(transactions)} sample transactions")
        
        # Create sample exchange rates
        exchange_rates = [
            {
                "pair": "USD/ARS",
                "value": Decimal("1340.50"),
                "source": "dolarapi_blue",
                "fetched_at": now - timedelta(hours=1)
            },
            {
                "pair": "USDT/ARS", 
                "value": Decimal("1350.00"),
                "source": "coingecko",
                "fetched_at": now - timedelta(hours=2)
            },
            {
                "pair": "BTC/USD",
                "value": Decimal("67500.00"),
                "source": "coingecko",
                "fetched_at": now - timedelta(minutes=30)
            },
            {
                "pair": "ETH/USD",
                "value": Decimal("2650.00"), 
                "source": "coingecko",
                "fetched_at": now - timedelta(minutes=30)
            }
        ]
        
        for rate_data in exchange_rates:
            await ExchangeRateCRUD.create(session, **rate_data)
        
        print(f"✅ Created {len(exchange_rates)} sample exchange rates")
        
        print("🎉 Database seeding completed successfully!")


async def clear_database():
    """Clear all data from database (for testing)."""
    async with async_session_maker() as session:
        print("🧹 Clearing database...")
        
        # Delete in reverse order due to foreign key constraints
        await session.execute("DELETE FROM exchange_rates")
        await session.execute("DELETE FROM transactions") 
        await session.execute("DELETE FROM account_balances")
        await session.execute("DELETE FROM accounts")
        await session.commit()
        
        print("✅ Database cleared successfully!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_database())
    else:
        asyncio.run(seed_database())