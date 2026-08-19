import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.shared.redis.client import get_redis
from app.shared.s3.client import s3_client

MAX_PROJECT_STORAGE_BYTES = 50 * 1024 * 1024  # 50 MB
REDIS_CACHE_TTL = 3600  # 1 час


class StorageService:
    @staticmethod
    def _get_cache_key(project_id: uuid.UUID) -> str:
        return f"project:{project_id}:storage_bytes"

    @classmethod
    async def get_project_size(cls, project_id: uuid.UUID) -> int:
        """Возвращает размер проекта из Redis-кэша, а при промахе считает из S3."""
        cache_key = cls._get_cache_key(project_id)
        redis = await get_redis()

        # Проверяем кэш в Redis
        cached_size = await redis.get(cache_key)
        if cached_size is not None:
            return int(cached_size)

        # Если в кэше нет — считаем напрямую из S3 и сохраняем
        total_size = await s3_client.get_project_total_size(project_id)
        await redis.set(cache_key, str(total_size), ex=REDIS_CACHE_TTL)
        return total_size

    @classmethod
    async def save_file(cls, file: UploadFile, project_id: uuid.UUID) -> str:
        """Проверяет лимит и загружает файл в S3, инкрементируя счетчик в Redis."""
        file_size = file.size or 0

        current_size = await cls.get_project_size(project_id)
        if current_size + file_size > MAX_PROJECT_STORAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Превышен лимит хранилища проекта (Максимум 50 MB)",
            )

        file_extension = Path(file.filename).suffix if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        s3_path = f"projects/{project_id}/{unique_filename}"

        # Загружаем файл в S3
        uploaded_path = await s3_client.upload_file(file, s3_path)

        # Инкрементируем размер в Redis
        cache_key = cls._get_cache_key(project_id)
        redis = await get_redis()
        if await redis.exists(cache_key):
            await redis.incrby(cache_key, file_size)

        return uploaded_path

    @classmethod
    async def get_storage_stats(cls, project_id: uuid.UUID) -> dict[str, float | int | str]:
        """Статистика диска с поддержкой кэша."""
        used_bytes = await cls.get_project_size(project_id)
        return {
            "project_id": str(project_id),
            "used_bytes": used_bytes,
            "used_mb": round(used_bytes / (1024 * 1024), 2),
            "max_mb": 50,
            "usage_percentage": round((used_bytes / MAX_PROJECT_STORAGE_BYTES) * 100, 2),
        }


storage_service = StorageService()
