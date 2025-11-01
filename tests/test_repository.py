import pytest
import asyncpg
from datetime import date
from app.repositories.capacity_repository import CapacityRepository


@pytest.mark.asyncio
async def test_repository_fetch_capacity(init_db, database_url):
    conn = await asyncpg.connect(database_url)
    try:
        repo = CapacityRepository()
        results = await repo.fetch_capacity(conn, date(2024, 1, 1), date(2024, 3, 31))
        assert isinstance(results, list)
        assert len(results) >= 1

        sample = results[0]
        assert "week_start_date" in sample
        assert "week_no" in sample
        assert "offered_capacity_teu" in sample
        assert "offered_capacity_teu_4w_rolling_avg" in sample
    finally:
        await conn.close()
