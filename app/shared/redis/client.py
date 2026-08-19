import redis.asyncio as redis
from app.shared.config.settings import settings

redis_client: redis.Redis | None = None


async def init_redis() -> None:
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.aclose()


async def get_redis() -> redis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    return redis_client