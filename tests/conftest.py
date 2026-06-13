import sys
import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

@pytest.fixture
def anyio_backend():
    return 'asyncio'

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

@pytest.fixture
async def db_session():
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        echo=False,
    )
    
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()