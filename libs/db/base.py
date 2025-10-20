from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from libs.db.config import settings

Base = declarative_base()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=NullPool,  # Use NullPool to avoid event loop conflicts with Flask async
)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
