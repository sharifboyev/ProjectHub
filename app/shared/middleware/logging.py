import logging
import time
import uuid
from typing import Any

logger = logging.getLogger("api_logger")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class LoggingMiddleware:
    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        async def send_wrapper(message: Any) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            
            await send(message)
            
            if message["type"] == "http.response.body":
                process_time = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"RequestID: {request_id} | "
                    f"Method: {scope['method']} | "
                    f"Path: {scope['path']} | "
                    f"Time: {process_time:.2f}ms"
                )

        await self.app(scope, receive, send_wrapper)
