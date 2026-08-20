from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.shared.config.settings import settings

arq_pool: ArqRedis | None = None


async def get_arq_pool() -> ArqRedis:
    global arq_pool
    if arq_pool is None:
        arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    return arq_pool


async def close_arq_pool() -> None:
    global arq_pool
    if arq_pool:
        await arq_pool.close()
        arq_pool = None