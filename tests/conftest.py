"""Pytest fixtures for fast-api-archon."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.database import get_async_db
from app.main import app
from app.models.base import Base
from app.services.seed_data import seed_database

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def override_get_async_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_async_db] = override_get_async_db


@pytest_asyncio.fixture(scope="function")
async def client():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as db:
        await seed_database(db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def auth_token(client: AsyncClient):
    resp = await client.post(
        "/register",
        json={"name": "Test Candidate", "email": "candidate@archon.dev", "password": "Password123!"},
    )
    if resp.status_code == 201:
        return resp.json()["access_token"]
    login_resp = await client.post(
        "/login",
        json={"email": "candidate@archon.dev", "password": "Password123!"},
    )
    return login_resp.json()["access_token"]
