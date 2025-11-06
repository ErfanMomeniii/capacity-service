import os
import json
import decimal
from datetime import date, datetime

import asyncpg
import redis.asyncio as aioredis
from fastapi import HTTPException

from app.exceptions import CapacityValidationException, CapacityDatabaseException
from app.repositories.capacity_repository import CapacityRepository
from app.core.monitoring import CACHE_HITS_COUNT, CACHE_MISSES_COUNT
from app.core import logging

logger = logging.get_logger(__name__)

# Cache time-to-live for Redis in seconds (default: 6 hours)
CACHE_TTL_SECONDS = int(os.getenv("CAPACITY_CACHE_TTL", 6 * 60 * 60))


class CapacityService:
    """Encapsulates business logic for computing offered capacity with integrated caching.

    This service layer isolates caching, validation, and repository interactions
    to maintain clean separation between API handlers and data-access logic.
    """

    def __init__(self):
        # Repository layer handles direct DB queries
        self.repo = CapacityRepository()
        # Initialize Redis connection (used for caching responses)
        self.redis = self._init_redis()

    # ------------------------------------------------------------
    # Redis Initialization
    # ------------------------------------------------------------
    def _init_redis(self) -> aioredis.Redis:
        """Create a Redis client instance from environment configuration."""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD", None)

        # Support both password-protected and open Redis instances
        redis_url = f"redis://{':' + redis_password + '@' if redis_password else ''}{redis_host}:{redis_port}/{redis_db}"

        try:
            client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}, DB={redis_db}")
            return client
        except Exception as e:
            # Graceful degradation: continue without Redis
            logger.warning(f"Failed to initialize Redis: {e}")
            return None

    # ------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------
    def _make_cache_key(self, start: date, end: date) -> str:
        """Generate a deterministic Redis cache key for the given date range."""
        return f"capacity:{start.isoformat()}:{end.isoformat()}"

    def _serialize_for_cache(self, data: list[dict]) -> str:
        """Convert data into a JSON-safe string for Redis storage.

        Handles non-JSON types such as Decimal and datetime objects.
        """

        def converter(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            raise TypeError(f"Type {type(obj)} not serializable")

        return json.dumps(data, default=converter)

    # ------------------------------------------------------------
    # Core Business Method
    # ------------------------------------------------------------
    async def get_capacity_rolling_average(
        self, conn: asyncpg.Connection, start: date, end: date
    ) -> list[dict]:
        """Retrieve offered capacity between two dates, using cache when available.

        The method enforces input validation, uses Redis as a performance layer,
        and falls back to the database if the cache is unavailable or empty.
        """
        # Validate input date range before proceeding
        if start > end:
            raise CapacityValidationException("date_from must be <= date_to")

        key = self._make_cache_key(start, end)

        # Attempt cache read if Redis is available
        if self.redis:
            try:
                cached = await self.redis.get(key)
                if cached:
                    logger.info(f"Cache hit for {key}")
                    CACHE_HITS_COUNT.inc()
                    return json.loads(cached)
                CACHE_MISSES_COUNT.inc()
                logger.info(f"Cache miss for {key}")
            except Exception as e:
                # Avoid interrupting business flow due to cache errors
                logger.warning(f"Redis unavailable, skipping cache: {e}")

        # Cache miss or Redis unavailable → query the database
        try:
            data = await self.repo.fetch_capacity(conn, start, end)
        except Exception as exc:
            raise CapacityDatabaseException(f"Database operation failed: {exc}") from exc

        # Persist fresh data in cache for future requests
        if self.redis:
            try:
                await self.redis.setex(key, CACHE_TTL_SECONDS, self._serialize_for_cache(data))
                logger.info(f"Cached result for {key} (TTL={CACHE_TTL_SECONDS}s)")
            except Exception as e:
                logger.warning(f"Failed to write to Redis cache for {key}: {e}")

        return data
