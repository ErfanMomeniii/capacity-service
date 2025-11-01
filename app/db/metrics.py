from functools import wraps
import time
from typing import Callable, Any
import logging
from prometheus_client import Histogram

logger = logging.getLogger(__name__)

QUERY_DURATION = Histogram(
    'capacity_query_duration_seconds',
    'Time spent executing database queries',
    ['query_name']
)


def monitor_query(query_name: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                QUERY_DURATION.labels(query_name=query_name).observe(duration)

                if duration > 1.0:  # Log slow queries
                    logger.warning(
                        "Slow query detected",
                        extra={
                            "query_name": query_name,
                            "duration": duration,
                            "args": args,
                            "kwargs": kwargs
                        }
                    )
                return result
            except Exception as e:
                logger.error(
                    "Query failed",
                    extra={
                        "query_name": query_name,
                        "error": str(e),
                        "args": args,
                        "kwargs": kwargs
                    }
                )
                raise

        return wrapper

    return decorator
