import logging
import time
from typing import Any

logger = logging.getLogger("projecthub.access")


class RequestLoggingMiddleware:
    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        async def send_wrapper(message: Any) -> None:
            await send(message)
            
            if message["type"] == "http.response.body":
                process_time_ms = (time.perf_counter() - start_time) * 1000
                client_host = "unknown"
                if "client" in scope and scope["client"]:
                    client_host = scope["client"][0]

                logger.info(
                    f"{client_host} - '{scope['method']} {scope['path']}' "
                    f"Completed in {process_time_ms:.2f}ms"
                )

        await self.app(scope, receive, send_wrapper)
