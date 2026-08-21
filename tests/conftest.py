from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.main import main_app
from app.shared.config.settings import settings
from app.shared.db.session import Base, get_db
from app.shared.tasks import get_arq_pool

TEST_DATABASE_URL = settings.DATABASE_URL.replace("projecthub", "projecthub_test")


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Единый Engine на всю тестовую сессию."""
    engine = create_async_engine(TEST_DATABASE_URL, future=True, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Предоставляет изолированную сессию БД для каждого теста."""
    session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with session_maker() as session:
        yield session
        await session.close()

    # Очистка таблиц после каждого теста для изоляции
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
        await conn.commit()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент для вызова API."""

    main_app.dependency_overrides[get_db] = lambda: db_session

    transport = ASGITransport(app=main_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    main_app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def mock_redis():
    """Мокирование клиента Redis."""
    fake_redis = AsyncMock()
    fake_redis.get = AsyncMock(return_value=None)
    fake_redis.set = AsyncMock(return_value=True)
    fake_redis.delete = AsyncMock(return_value=1)
    fake_redis.keys = AsyncMock(return_value=[])
    fake_redis.aclose = AsyncMock()
    fake_redis.exists = AsyncMock(return_value=False)
    fake_redis.incrby = AsyncMock(return_value=0)

    with (
        patch("app.documents.service.get_redis", AsyncMock(return_value=fake_redis)),
        patch("app.shared.redis.client.get_redis", AsyncMock(return_value=fake_redis)),
        patch("app.shared.storage.get_redis", AsyncMock(return_value=fake_redis)),
    ):
        yield fake_redis


@pytest_asyncio.fixture(autouse=True)
async def mock_s3_client():
    """Мокирование S3/MinIO клиентов."""
    mock_s3 = AsyncMock()
    mock_s3.upload_file = AsyncMock(
        return_value="https://mock-s3.local/projecthub-documents/test.txt"
    )
    mock_s3.delete_file = AsyncMock(return_value=True)
    mock_s3.download_file = AsyncMock(return_value=b"mock content")
    mock_s3.get_project_total_size = AsyncMock(return_value=0)
    mock_s3.ensure_bucket_exists = AsyncMock(return_value=None)
    # Мокируем новый метод
    mock_s3.generate_presigned_url = AsyncMock(
        return_value="https://mock-s3.local/presigned-url-test"
    )

    with (
        patch("app.documents.service.s3_client", mock_s3),
        patch("app.shared.storage.s3_client", mock_s3),
        patch("app.main.s3_client", mock_s3),
        patch("app.shared.s3.client.s3_client", mock_s3),
    ):
        yield mock_s3


@pytest.fixture(autouse=True)
def override_arq_pool():
    """Мокирование ARQ на экземпляре main_app."""
    mock_arq = AsyncMock()
    mock_arq.enqueue_job = AsyncMock(return_value=AsyncMock(job_id="test_job_123"))

    main_app.dependency_overrides[get_arq_pool] = lambda: mock_arq
    yield mock_arq
    main_app.dependency_overrides.pop(get_arq_pool, None)

