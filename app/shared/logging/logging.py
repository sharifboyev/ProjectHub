import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("projecthub.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time_ms = (time.perf_counter() - start_time) * 1000
        client_host = request.client.host if request.client else "unknown"

        logger.info(
            f"{client_host} - '{request.method} {request.url.path}' "
            f"Status: {response.status_code} "
            f"Completed in {process_time_ms:.2f}ms"
        )

        response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
        return response