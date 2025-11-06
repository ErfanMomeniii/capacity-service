import time
from app.core import logging
from functools import wraps
from typing import Callable, Any
from prometheus_client import Histogram, Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.routing import APIRouter

logger = logging.get_logger(__name__)


# ------------------------------------------------------------
# Prometheus Metrics Definitions
# ------------------------------------------------------------
# Request-level metrics
REQUEST_DURATION = Histogram(
    "capacity_request_duration_seconds",
    "Request latency (seconds)",
    ["method", "path", "status_code"],
)

REQUEST_COUNT = Counter(
    "capacity_request_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)

# Cache metrics to monitor cache efficiency
CACHE_HITS_COUNT = Counter(
    "capacity_cache_hits",
    "Cache hit count"
)

CACHE_MISSES_COUNT = Counter(
    "capacity_cache_misses",
    "Cache miss count"
)

# Query-level performance monitoring
QUERY_DURATION = Histogram(
    "capacity_query_duration_seconds",
    "Database query duration (seconds)",
    ["query_name"],
)


# ------------------------------------------------------------
# Query Monitoring Decorator
# ------------------------------------------------------------
def monitor_query(query_name: str):
    """
    Decorator to measure database query execution time and log slow queries.

    Responsibilities:
    - Updates Prometheus histogram for query duration.
    - Logs queries exceeding 1 second as warnings.
    - Captures and logs query errors without disrupting business logic flow.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Record duration for Prometheus
                QUERY_DURATION.labels(query_name=query_name).observe(duration)

                # Warn on slow queries for operational observability
                if duration > 1.0:
                    logger.warning(
                        "Slow query detected",
                        extra={
                            "query_name": query_name,
                            "duration": round(duration, 4),
                        },
                    )

                return result

            except Exception as e:
                # Capture query failures in structured logs
                logger.error(
                    "Query failed",
                    extra={
                        "query_name": query_name,
                        "error": str(e),
                    },
                )
                raise

        return wrapper

    return decorator


# ------------------------------------------------------------
# Prometheus Metrics Endpoint
# ------------------------------------------------------------
router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:
    """
    Expose Prometheus metrics endpoint for scraping.

    Provides all defined metrics including:
    - Request latency and count
    - Cache hits/misses
    - Query execution durations
    """
    data = generate_latest()
    return Response(data, media_type=CONTENT_TYPE_LATEST)
