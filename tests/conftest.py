import io
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.shared.config.settings import settings
from app.shared.db.session import Base, get_db

TEST_DATABASE_URL = settings.DATABASE_URL.replace("projecthub", "projecthub_test")


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    """Создает тестовые таблицы перед запуском сессии и удаляет их после."""
    engine_test = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine_test.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Предоставляет изолированную транзакцию БД для каждого теста."""
    engine_test = create_async_engine(TEST_DATABASE_URL, future=True)
    testing_session_local = async_sessionmaker(
        engine_test,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with testing_session_local() as session:
        yield session
        await session.rollback()
    await engine_test.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент для вызова API с подменяемой сессией БД и запуском lifespan."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    # Запускаем контекст lifespan, чтобы отработали стартовые обработчики приложения
    async with app.router.lifespan_context(app):
        async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def mock_redis():
    """Мокирование клиента Redis по всем местам прямого импорта."""
    fake_redis = AsyncMock()
    fake_redis.get = AsyncMock(return_value=None)
    fake_redis.set = AsyncMock(return_value=True)
    fake_redis.delete = AsyncMock(return_value=1)
    fake_redis.keys = AsyncMock(return_value=[])
    fake_redis.aclose = AsyncMock()

    with patch("app.documents.service.get_redis", AsyncMock(return_value=fake_redis)), \
            patch("app.shared.redis.client.get_redis", AsyncMock(return_value=fake_redis)):
        yield fake_redis


@pytest_asyncio.fixture(autouse=True)
async def mock_s3_client():
    """Мокирование S3/MinIO клиентов."""
    with patch("app.documents.service.s3_client") as mock_s3:
        mock_s3.upload_file = AsyncMock(
            return_value="https://mock-s3.local/projecthub-documents/test.txt"
        )
        mock_s3.delete_file = AsyncMock(return_value=True)
        yield mock_s3