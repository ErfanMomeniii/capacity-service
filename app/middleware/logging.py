import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        request.state.request_id = request_id

        response = await call_next(request)

        duration = time.time() - start_time

        logger.info(
            "Request processed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration": duration,
                "status_code": response.status_code
            }
        )

        # Add request_id to response headers
        response.headers["X-Request-ID"] = request_id
        return response