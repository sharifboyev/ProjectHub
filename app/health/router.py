# app/health/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.db.session import get_db
from app.shared.redis.client import get_redis
from app.shared.s3.client import s3_client

router = APIRouter(prefix="/health", tags=["Healthcheck"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """Простейшая liveness-проба: сервис запущен и отвечает."""
    return {"status": "live"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness-проба: проверяет подключение к PostgreSQL, Redis и S3."""
    errors = []

    # 1. Проверка PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        errors.append(f"PostgreSQL unreachable: {e}")

    # 2. Проверка Redis
    try:
        redis = await get_redis()
        await redis.ping()
    except Exception as e:
        errors.append(f"Redis unreachable: {e}")

    # 3. Проверка S3 MinIO
    try:
        await s3_client.ensure_bucket_exists()
    except Exception as e:
        errors.append(f"S3/MinIO unreachable: {e}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "errors": errors},
        )

    return {"status": "ready", "services": {"postgres": "ok", "redis": "ok", "s3": "ok"}}