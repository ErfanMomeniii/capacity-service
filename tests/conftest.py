import os
import sys
import pytest
import asyncio
import asyncpg
from httpx import AsyncClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app



@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def database_url():
    return "postgresql://postgres:postgres@localhost:5432/test_db"


@pytest.fixture
async def app_client(init_db, database_url):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
async def init_db(database_url):
    conn = await asyncpg.connect(database_url)
    try:
        # Create test database schema
        with open("db/schema.sql", "r") as f:
            schema_sql = f.read()
        await conn.execute(schema_sql)

        # Insert test data
        insert_sql = """
        INSERT INTO sailings (
            service_version_and_roundtrip_identfiers,
            origin_service_version_and_master,
            destination_service_version_and_master,
            vessel_identifier,
            origin_port_code,
            destination_port_code,
            origin_at_utc,
            offered_capacity_teu
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """

        test_data = [
            ("SRV001", "china_main", "north_europe_main", "VSL001", "CNSHA",
             "NLRTM", "2024-01-03 08:00:00+00", 20000),
            ("SRV002", "china_main", "north_europe_main", "VSL002", "CNSHA",
             "NLAMS", "2024-01-17 08:00:00+00", 22000),
            ("SRV003", "china_main", "north_europe_main", "VSL003", "CNSHA",
             "DEHAM", "2024-02-21 08:00:00+00", 26000),
            ("SRV004", "china_main", "north_europe_main", "VSL004", "CNSHA",
             "GBFXT", "2024-03-05 08:00:00+00", 19000),
            ("SRV005", "china_main", "north_europe_main", "VSL005", "CNYTN",
             "FRLEH", "2024-03-19 08:00:00+00", 21000),
        ]

        for row in test_data:
            await conn.execute(insert_sql, *row)

        yield
    finally:
        await conn.close()
