from fastapi import FastAPI

import app.users.models  # noqa: F401
import app.projects.models  # noqa: F401
import app.documents.models  # noqa: F401

from app.shared.config.settings import settings
from app.shared.middleware.logging import LoggingMiddleware
from app.auth.router import router as auth_router
from app.projects.router import router as projects_router
from app.documents.router import router as documents_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Подключаем Middleware логов
app.add_middleware(LoggingMiddleware)

# Подключаем эндпоинты
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(documents_router)  # <-- 2. ДОБАВИЛИ ЭТУ СТРОКУ!


@app.get("/health", tags=["Healthcheck"])
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "project": settings.PROJECT_NAME}