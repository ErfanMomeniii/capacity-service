from typing import Optional
from asyncpg.pool import Pool
import asyncpg
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class DBConfig(BaseModel):
    dsn: str
    min_size: int = 5
    max_size: int = 20
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0  # 5 minutes

class DatabasePool:
    def __init__(self):
        self.pool: Optional[Pool] = None
        self._config: Optional[DBConfig] = None

    async def initialize(self, config: DBConfig) -> None:
        self._config = config
        try:
            self.pool = await asyncpg.create_pool(
                dsn=config.dsn,
                min_size=config.min_size,
                max_size=config.max_size,
                max_queries=config.max_queries,
                max_inactive_connection_lifetime=config.max_inactive_connection_lifetime,
                setup=self._setup_connection
            )
            logger.info(
                "Database pool initialized",
                extra={
                    "min_size": config.min_size,
                    "max_size": config.max_size
                }
            )
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {str(e)}")
            raise

    @staticmethod
    async def _setup_connection(conn: asyncpg.Connection) -> None:
        await conn.execute('SET timezone TO "UTC"')

    async def check_health(self) -> bool:
        if not self.pool:
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('SELECT 1')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False