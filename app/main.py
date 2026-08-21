import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.auth.router import router as auth_router
from app.documents.router import router as documents_router
from app.health.router import router as health_router
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
    # Shutdown: Закрытие соединения с Redis и ARQ
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

# Подключение роутеров
main_app.include_router(auth_router)
main_app.include_router(projects_router)
main_app.include_router(documents_router)
main_app.include_router(health_router)

# Prometheus Instrumentator для экспорта /metrics
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=False,
    should_instrument_requests_inprogress=True,
)
instrumentator.instrument(main_app).expose(main_app, endpoint="/metrics")