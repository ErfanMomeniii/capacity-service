from __future__ import annotations

import os
import logging
from typing import AsyncGenerator, Optional, Any

import asyncpg
from asyncpg import Pool, Connection
from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DBConfig(BaseModel):
    """Configuration model for asyncpg database connection pool."""
    dsn: str = Field(..., description="PostgreSQL DSN string, e.g., postgres://user:pass@host:port/dbname")
    min_size: int = Field(5, ge=1, description="Minimum number of connections in the pool")
    max_size: int = Field(20, ge=1, description="Maximum number of connections in the pool")
    max_queries: int = Field(50000, description="Maximum number of queries per connection before recycling")
    max_inactive_connection_lifetime: float = Field(300.0, description="Max idle time (seconds) before closing connection")

    @classmethod
    def from_env(cls) -> "DBConfig":
        """Load configuration from environment variables."""
        dsn = os.getenv("DATABASE_URL")
        if not dsn:
            raise RuntimeError("DATABASE_URL environment variable is required")
        return cls(dsn=dsn)


class DatabasePool:
    """Manages asyncpg connection pool lifecycle and provides health checks."""

    def __init__(self) -> None:
        self.pool: Optional[Pool] = None
        self.config: Optional[DBConfig] = None

    async def initialize(self, config: Optional[DBConfig] = None) -> None:
        """Initialize the asyncpg connection pool."""
        self.config = config or DBConfig.from_env()
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.config.dsn,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                setup=self._setup_connection
            )
            logger.info(
                "✅ Database connection pool initialized",
                extra={"min_size": self.config.min_size, "max_size": self.config.max_size}
            )
        except Exception as e:
            logger.exception("❌ Failed to initialize database pool")
            raise RuntimeError(f"Database initialization failed: {e}") from e

    @staticmethod
    async def _setup_connection(conn: Connection) -> None:
        """Setup each connection in the pool (e.g., timezone, settings)."""
        await conn.execute('SET timezone TO "UTC"')

    async def check_health(self) -> bool:
        """Perform a lightweight health check by executing a trivial query."""
        if not self.pool:
            logger.warning("Database pool not initialized")
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def close(self) -> None:
        """Gracefully close the pool."""
        if self.pool:
            await self.pool.close()
            logger.info("🔒 Database pool closed")

db_pool = DatabasePool()

async def init_db_pool(app: FastAPI) -> None:
    """Attach initialized DB pool to FastAPI app state."""
    await db_pool.initialize()
    app.state.db_pool = db_pool.pool

async def close_db_pool(app: FastAPI) -> None:
    """Close DB pool on FastAPI shutdown."""
    await db_pool.close()


async def get_conn() -> AsyncGenerator[Connection, Any]:
    """
    Dependency for routes: yields an asyncpg.Connection.
    Example usage:
        @router.get("/users")
        async def list_users(conn: Connection = Depends(get_conn)):
            rows = await conn.fetch("SELECT * FROM users")
            return [dict(r) for r in rows]
    """
    if db_pool.pool is None:
        raise RuntimeError("Database pool is not initialized")
    async with db_pool.pool.acquire() as conn:
        yield conn
