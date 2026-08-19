from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.shared.config.settings import settings

# Асинхронный движок
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency для получения сессии БД на время запроса."""
    async with AsyncSessionLocal() as session:
        yield session
