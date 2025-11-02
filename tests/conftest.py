import os
import sys
import asyncio
import asyncpg
import pytest
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import app

# --------------------------
# Event loop for async tests
# --------------------------
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# --------------------------
# Database URL fixture
# --------------------------
@pytest.fixture(scope="session")
def database_url():
    return "postgresql://postgres:postgres@localhost:5432/test_db"

# --------------------------
# Database setup fixture
# --------------------------
@pytest.fixture(scope="session")
async def init_db(database_url):
    conn = await asyncpg.connect(database_url)
    try:
        # Create schema
        with open("db/schema.sql", "r") as f:
            schema_sql = f.read()
        await conn.execute(schema_sql)

        # Insert test data
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
            ("china_main", "north_europe_main", "NLRTM", "CNSHA", "SRV001", "china_main", "north_europe_main",
             datetime.fromisoformat("2024-01-03T08:00:00+00:00"), 20000),
            ("china_main", "north_europe_main", "NLAMS", "CNSHA", "SRV002", "china_main", "north_europe_main",
             datetime.fromisoformat("2024-01-17T08:00:00+00:00"), 22000),
            ("china_main", "north_europe_main", "DEHAM", "CNSHA", "SRV003", "china_main", "north_europe_main",
             datetime.fromisoformat("2024-02-21T08:00:00+00:00"), 26000),
            ("china_main", "north_europe_main", "GBFXT", "CNSHA", "SRV004", "china_main", "north_europe_main",
             datetime.fromisoformat("2024-03-05T08:00:00+00:00"), 19000),
            ("china_main", "north_europe_main", "CNYTN", "FRLEH", "SRV005", "china_main", "north_europe_main",
             datetime.fromisoformat("2024-03-19T08:00:00+00:00"), 21000),
        ]
        for row in test_data:
            await conn.execute(insert_sql, *row)

        yield
    finally:
        await conn.close()

# --------------------------
# FastAPI TestClient fixture
# --------------------------
@pytest.fixture
async def app_client(init_db, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db")
    with TestClient(app) as client:
        yield client