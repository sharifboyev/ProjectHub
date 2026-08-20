import logging
from typing import Any

logger = logging.getLogger(__name__)


async def process_document_task(ctx: dict[str, Any], document_id: int) -> str:
    logger.info(f"Processing document_id={document_id}")
    # Логика обработки документа или очистки кэша
    return f"Document {document_id} processed"