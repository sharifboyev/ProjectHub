import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Импорт моделей для корректной инициализации SQLAlchemy / Alembic
from app.auth.router import router as auth_router
from app.documents.router import router as documents_router
from app.projects.router import router as projects_router
from app.shared.config.settings import settings
from app.shared.logging.logging import RequestLoggingMiddleware
from app.shared.redis.client import close_redis, init_redis
from app.shared.s3.client import s3_client
from app.shared.tasks import close_arq_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Подключение к Redis и проверка/создание S3-бакета
    await init_redis()
    await s3_client.ensure_bucket_exists()
    yield
    # Shutdown: Закрытие соединения с Redis
    await close_redis()
    await close_arq_pool()


main_app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware
main_app.add_middleware(RequestLoggingMiddleware)

# Подключение всех роутеров
main_app.include_router(auth_router)
main_app.include_router(projects_router)
main_app.include_router(documents_router)


@main_app.get("/health", tags=["Healthcheck"])
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "project": settings.PROJECT_NAME}
