import pytest
import asyncpg
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from app.repositories.capacity_repository import CapacityRepository
from app.exceptions import CapacityDatabaseException
from conftest import setup_db


@pytest.mark.asyncio
class TestCapacityRepository:

    async def _prepare_db(self, database_url):
        await setup_db(database_url)

    async def test_fetch_capacity_success(self, database_url):
        await self._prepare_db(database_url)

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

            week_no_value = first_row["week_no"]
            if isinstance(week_no_value, Decimal):
                week_no_value = int(week_no_value)
            assert isinstance(week_no_value, int)

            assert isinstance(first_row["week_start_date"], date)
            assert isinstance(first_row["offered_capacity_teu"], (int, float, Decimal))
            assert isinstance(first_row["offered_capacity_teu_4w_rolling_avg"], (int, float, Decimal))

            assert all(
                results[i]["week_start_date"] <= results[i + 1]["week_start_date"]
                for i in range(len(results) - 1)
            )
        finally:
            await conn.close()

    async def test_fetch_capacity_invalid_date_range(self, database_url):
        await self._prepare_db(database_url)

        conn = await asyncpg.connect(database_url)
        try:
            repo = CapacityRepository()
            results = await repo.fetch_capacity(conn, date(2024, 3, 31), date(2024, 1, 1))
            assert isinstance(results, list)
            assert len(results) == 0
        finally:
            await conn.close()

    async def test_fetch_capacity_future_dates(self, database_url):
        await self._prepare_db(database_url)

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
        conn = await asyncpg.connect(database_url)
        await conn.close()
        with pytest.raises(CapacityDatabaseException):
            await repo.fetch_capacity(conn, date(2024, 1, 1), date(2024, 3, 31))

    async def test_fetch_capacity_monitor_decorator_success(self):
        """monitor_query wrapper should allow normal successful execution."""
        repo = CapacityRepository()
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {"week_start_date": date(2024, 1, 1), "week_no": 1, "offered_capacity_teu": 20000,
             "offered_capacity_teu_4w_rolling_avg": 20000}
        ]

        results = await repo.fetch_capacity(mock_conn, date(2024, 1, 1), date(2024, 3, 31))

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["week_no"] == 1

    async def test_fetch_capacity_monitor_decorator_slow(self):
        """Simulate a slow query without real sleep — ensure monitor logs slow queries safely."""
        repo = CapacityRepository()
        mock_conn = AsyncMock()

        async def fetch_ok(*_):
            return [
                {
                    "week_start_date": date(2024, 1, 8),
                    "week_no": 2,
                    "offered_capacity_teu": 18000,
                    "offered_capacity_teu_4w_rolling_avg": 19000,
                }
            ]

        mock_conn.fetch.side_effect = fetch_ok

        time_calls = iter([1000.0, 1002.0])

        def safe_time():
            try:
                return next(time_calls)
            except StopIteration:
                return 1002.0

        with patch("app.core.monitoring.time.time", side_effect=safe_time):
            results = await repo.fetch_capacity(mock_conn, date(2024, 1, 1), date(2024, 3, 31))

        assert len(results) == 1
        assert results[0]["week_no"] == 2

    async def test_fetch_capacity_monitor_decorator_raises_capacity_db_exception_on_closed(self):
        """If underlying exception text contains 'closed', repository should raise CapacityDatabaseException."""
        repo = CapacityRepository()
        mock_conn = AsyncMock()

        async def raise_closed(*_args, **_kwargs):
            raise Exception("Connection is closed")

        mock_conn.fetch.side_effect = raise_closed

        with pytest.raises(CapacityDatabaseException):
            await repo.fetch_capacity(mock_conn, date(2024, 1, 1), date(2024, 3, 31))
