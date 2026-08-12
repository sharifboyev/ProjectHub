from fastapi import FastAPI
import app.users.models
import app.projects.models
import app.documents.models
from app.shared.config.settings import settings
from app.shared.middleware.logging import LoggingMiddleware
from app.auth.router import router as auth_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Подключаем Middleware логов
app.add_middleware(LoggingMiddleware)

# Подключаем эндпоинты аутентификации
app.include_router(auth_router)


@app.get("/health", tags=["Healthcheck"])
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "project": settings.PROJECT_NAME}