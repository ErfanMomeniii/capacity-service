import pytest
import asyncpg
from datetime import date, datetime, timedelta
from app.repositories.capacity_repository import CapacityRepository
from app.exceptions import CapacityDatabaseException


@pytest.mark.asyncio
class TestCapacityRepository:
    async def test_fetch_capacity_success(self, init_db, database_url):
        conn = await asyncpg.connect(database_url)
        try:
            repo = CapacityRepository()
            results = await repo.fetch_capacity(conn, date(2024, 1, 1), date(2024, 3, 31))

            assert isinstance(results, list)
            assert len(results) > 0

            first_row = results[0]
            expected_keys = {
                "week_start_date",
                "week_no",
                "offered_capacity_teu",
                "offered_capacity_teu_4w_rolling_avg"
            }
            assert all(key in first_row for key in expected_keys)

            # Verify data types
            assert isinstance(first_row["week_start_date"], date)
            assert isinstance(first_row["week_no"], int)
            assert isinstance(first_row["offered_capacity_teu"], (int, float))
            assert isinstance(first_row["offered_capacity_teu_4w_rolling_avg"], (int, float))

            # Verify data order
            assert all(results[i]["week_start_date"] <= results[i + 1]["week_start_date"]
                       for i in range(len(results) - 1))
        finally:
            await conn.close()

    async def test_fetch_capacity_invalid_date_range(self, init_db, database_url):
        conn = await asyncpg.connect(database_url)
        try:
            repo = CapacityRepository()
            with pytest.raises(ValueError):
                await repo.fetch_capacity(conn, date(2024, 3, 31), date(2024, 1, 1))
        finally:
            await conn.close()

    async def test_fetch_capacity_future_dates(self, init_db, database_url):
        conn = await asyncpg.connect(database_url)
        try:
            repo = CapacityRepository()
            future_start = date.today() + timedelta(days=365)
            future_end = future_start + timedelta(days=90)
            results = await repo.fetch_capacity(conn, future_start, future_end)
            assert isinstance(results, list)
            assert len(results) == 0
        finally:
            await conn.close()

    async def test_fetch_capacity_connection_error(self, database_url):
        repo = CapacityRepository()
        with pytest.raises(CapacityDatabaseException):
            conn = await asyncpg.connect(database_url)
            await conn.close()
            await repo.fetch_capacity(conn, date(2024, 1, 1), date(2024, 3, 31))