import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.middleware.logging")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request logging and traceability.

    Responsibilities:
    - Assigns a unique request ID to every incoming request for distributed tracing.
    - Logs key request metadata including method, path, status code, and processing duration.
    - Attaches the request ID to the response headers for downstream observability.
    """

    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID for correlation across services
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Attach request ID to request.state for access in downstream handlers
        request.state.request_id = request_id

        try:
            # Continue the request lifecycle
            response = await call_next(request)
        finally:
            # Measure total request processing time
            duration = round(time.time() - start_time, 4)

            # Structured logging with request metadata
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

        # Add request ID header to response for external tracing
        response.headers["X-Request-ID"] = request_id
        return response
