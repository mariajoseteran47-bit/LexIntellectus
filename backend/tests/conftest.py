import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

# Override settings for testing
settings.POSTGRES_DB = "lexintellectus_test"

# Use the same URL but different DB
url_parts = str(settings.database_url).rsplit("/", 1)
TEST_DATABASE_URL = f"{url_parts[0]}/lexintellectus_test"

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine, class_=AsyncSession)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    from fastapi_limiter import FastAPILimiter
    from unittest.mock import AsyncMock
    FastAPILimiter.redis = AsyncMock()
    FastAPILimiter.redis.eval = AsyncMock(return_value=0)
    FastAPILimiter.redis.evalsha = AsyncMock(return_value=0)
    async def mock_identifier(*args, **kwargs):
        return "mock_ip"
    FastAPILimiter.identifier = mock_identifier
    async def mock_callback(*args, **kwargs):
        pass
    FastAPILimiter.http_callback = mock_callback

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
