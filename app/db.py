# app/db.py
from typing import AsyncGenerator
import os
import asyncpg
from fastapi import FastAPI

DATABASE_URL_ENV = "DATABASE_URL"


async def init_db_pool(app: FastAPI) -> None:
    """
    Initialize asyncpg pool and attach to app.state.db_pool
    """
    database_url = os.getenv(DATABASE_URL_ENV)
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set in environment")

    app.state.db_pool = await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=10)


async def close_db_pool(app: FastAPI) -> None:
    pool = getattr(app.state, "db_pool", None)
    if pool:
        await pool.close()


async def get_conn(app: FastAPI) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Dependency for routes: yields an asyncpg.Connection.
    Use as `conn=Depends(get_conn)` in routes.
    """
    pool = getattr(app.state, "db_pool", None)
    if pool is None:
        raise RuntimeError("Database pool is not initialized")
    async with pool.acquire() as conn:
        yield conn
