from arq.connections import RedisSettings

from app.documents.tasks import process_document_task
from app.shared.config.settings import settings


class WorkerSettings:
    functions = [process_document_task]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10