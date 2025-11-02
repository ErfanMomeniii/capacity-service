import time
from app.core import logging
from fastapi import Request, Response
from app.core.monitoring import REQUEST_DURATION, REQUEST_COUNT

logger = logging.get_logger(__name__)


async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

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
