import asyncio
import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.db.base import Base
from src.db.models import Account, AccountType, AccountBalance, Transaction, TransactionType


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_session():
    """Create a test database session."""
    # Use in-memory SQLite for tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def sample_account(async_session):
    """Create a sample account for testing."""
    account = Account(name="Test Account", type=AccountType.OTHER)
    async_session.add(account)
    await async_session.commit()
    await async_session.refresh(account)
    return account


@pytest.fixture
async def sample_account_with_balance(async_session):
    """Create a sample account with balance for testing."""
    account = Account(name="Test Account", type=AccountType.BANK)
    async_session.add(account)
    await async_session.flush()
    
    balance = AccountBalance(
        account_id=account.id,
        currency="USD",
        balance=Decimal("1000.00")
    )
    async_session.add(balance)
    await async_session.commit()
    await async_session.refresh(account)
    return account


@pytest.fixture
async def sample_transaction(async_session, sample_account):
    """Create a sample transaction for testing."""
    transaction = Transaction(
        type=TransactionType.INCOME,
        account_to_id=sample_account.id,
        currency="USD",
        amount=Decimal("500.00"),
        description="Test income",
        date=datetime.utcnow()
    )
    async_session.add(transaction)
    await async_session.commit()
    await async_session.refresh(transaction)
    return transaction