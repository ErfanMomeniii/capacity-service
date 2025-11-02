import os
import sys
import asyncio
from datetime import datetime
import asyncpg
import pytest_asyncio
from httpx import AsyncClient
from asgi_lifespan import LifespanManager

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
def database_url():
    return "postgresql://postgres:postgres@localhost:5432/test_db"

@pytest_asyncio.fixture(scope="session")
async def init_db(database_url):
    conn = await asyncpg.connect(database_url)
    try:
        with open("db/schema.sql", "r") as f:
            schema_sql = f.read()
        await conn.execute(schema_sql)

        insert_sql = """
        INSERT INTO sailings (
            origin,
            destination,
            origin_port_code,
            destination_port_code,
            service_version_and_roundtrip_identfiers,
            origin_service_version_and_master,
            destination_service_version_and_master,
            origin_at_utc,
            offered_capacity_teu
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """

        test_data = [
            ("NLRTM", "CNSHA", "NLRTM", "CNSHA", "SRV001", "china_main", "north_europe_main",
             datetime.fromisoformat("2024-01-03T08:00:00+00:00"), 20000),
            ("NLAMS", "CNSHA", "NLAMS", "CNSHA", "SRV002", "china_main", "north_europe_main",
             datetime.fromisoformat("2024-01-17T08:00:00+00:00"), 22000),
            ("DEHAM", "CNSHA", "DEHAM", "CNSHA", "SRV003", "china_main", "north_europe_main",
             datetime.fromisoformat("2024-02-21T08:00:00+00:00"), 26000),
            ("GBFXT", "CNSHA", "GBFXT", "CNSHA", "SRV004", "china_main", "north_europe_main",
             datetime.fromisoformat("2024-03-05T08:00:00+00:00"), 19000),
            ("CNYTN", "FRLEH", "CNYTN", "FRLEH", "SRV005", "china_main", "north_europe_main",
             datetime.fromisoformat("2024-03-19T08:00:00+00:00"), 21000),
        ]

        for row in test_data:
            await conn.execute(insert_sql, *row)

        yield
    finally:
        await conn.close()

@pytest_asyncio.fixture
async def app_client(init_db, database_url):
    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
