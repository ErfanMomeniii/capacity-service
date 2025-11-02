import pytest
import asyncpg
from httpx import AsyncClient
from datetime import date
from app.main import app
from app.db.pool import init_db_pool, close_db_pool


@pytest.mark.asyncio
class TestIntegration:
    async def test_full_capacity_flow(self, init_db, database_url):
        await init_db_pool(app)

        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/capacity?date_from=2024-01-01&date_to=2024-03-31"
                )
                assert response.status_code == 200
                data = response.json()

                assert len(data) > 0
                assert all(
                    date_from <= date.fromisoformat(item["week_start_date"]) <= date_to
                    for item in data
                )

                for i, item in enumerate(data):
                    if i >= 3:  # We should have enough data for rolling average
                        assert item["offered_capacity_teu_4w_rolling_avg"] is not None

                # Test data integrity
                assert all(
                    isinstance(item["offered_capacity_teu"], (int, float)) and
                    item["offered_capacity_teu"] > 0
                    for item in data
                )
        finally:
            await close_db_pool(app)

    async def test_database_connection_handling(self, init_db, database_url):
        await init_db_pool(app)

        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                tasks = []
                for _ in range(5):
                    tasks.append(
                        client.get("/capacity?date_from=2024-01-01&date_to=2024-03-31")
                    )

                responses = await asyncio.gather(*tasks)
                assert all(response.status_code == 200 for response in responses)
        finally:
            await close_db_pool(app)
