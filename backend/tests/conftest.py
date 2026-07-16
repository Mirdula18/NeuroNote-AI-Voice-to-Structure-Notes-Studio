"""Pytest configuration for NeuroNote AI backend tests."""

import asyncio
import os
from typing import AsyncGenerator

# Override database URL BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_neuronote.db"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import engine, Base
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
