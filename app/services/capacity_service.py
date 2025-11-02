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

CACHE_TTL_SECONDS = int(os.getenv("CAPACITY_CACHE_TTL", 6 * 60 * 60))  # 6 hours default


class CapacityService:
    """Business logic for offered capacity with Redis caching."""

    def __init__(self):
        self.repo = CapacityRepository()
        self.redis = self._init_redis()

    def _init_redis(self) -> aioredis.Redis:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        redis_url = f"redis://{':' + redis_password if redis_password else ''}{redis_host}:{redis_port}/{redis_db}"

        try:
            client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}, DB={redis_db}")
            return client
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}")
            return None

    def _make_cache_key(self, start: date, end: date) -> str:
        return f"capacity:{start.isoformat()}:{end.isoformat()}"

    def _serialize_for_cache(self, data: list[dict]) -> str:
        """Serialize data for Redis (handles date and Decimal)."""

        def converter(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            raise TypeError(f"Type {type(obj)} not serializable")

        return json.dumps(data, default=converter)

    async def get_capacity_rolling_average(
            self, conn: asyncpg.Connection, start: date, end: date
    ) -> list[dict]:
        if start > end:
            raise CapacityValidationException("date_from must be <= date_to")

        key = self._make_cache_key(start, end)

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
                logger.warning(f"Redis unavailable, skipping cache: {e}")

        try:
            data = await self.repo.fetch_capacity(conn, start, end)
        except Exception as exc:
            raise CapacityDatabaseException(f"Database operation failed: {exc}") from exc

        if self.redis:
            try:
                await self.redis.setex(key, CACHE_TTL_SECONDS, self._serialize_for_cache(data))
                logger.info(f"Cached result for {key} (TTL={CACHE_TTL_SECONDS}s)")
            except Exception as e:
                logger.warning(f"Failed to write to Redis cache for {key}: {e}")

        return data
