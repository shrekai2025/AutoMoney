"""Pytest configuration and fixtures"""

import pytest
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.config import settings
from app.models.base import Base
from app.core.deps import get_db


# Test database URL
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/automoney", "/automoney_test")


@pytest.fixture(scope="session")
def test_client():
    """Create a test client"""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
async def test_engine():
    """Create async test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async test database session"""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(test_db: AsyncSession):
    """Override get_db dependency for testing"""
    async def _get_test_db():
        yield test_db

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()
