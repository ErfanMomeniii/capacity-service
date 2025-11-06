import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core import logging
from app.core.monitoring import REQUEST_DURATION, REQUEST_COUNT

logger = logging.get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect and expose request-level metrics for observability.

    Responsibilities:
    - Measures request duration and increments request counters.
    - Adds structured logging for monitoring and debugging.
    - Supports Prometheus-style instrumentation via REQUEST_DURATION and REQUEST_COUNT.
    """

    async def dispatch(self, request: Request, call_next):
        # Record start time for duration measurement
        start_time = time.time()

        # Continue request lifecycle and capture the response
        response = await call_next(request)

        # Compute total request duration
        duration = time.time() - start_time

        # Update Prometheus metrics
        REQUEST_DURATION.labels(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        ).observe(duration)

        REQUEST_COUNT.labels(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        ).inc()

        # Structured logging for request observability
        logger.info(
            "Request metrics collected",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": round(duration, 4),
            },
        )

        return response
