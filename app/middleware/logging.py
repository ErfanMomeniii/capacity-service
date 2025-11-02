import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.middleware.logging")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        request.state.request_id = request_id

        try:
            response = await call_next(request)
        finally:
            duration = round(time.time() - start_time, 4)
            logger.info(
                "Request processed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                    "status_code": getattr(response, "status_code", 500),
                },
            )

        # Add request ID header for tracing
        response.headers["X-Request-ID"] = request_id
        return response
