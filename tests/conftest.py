import os
import sys
import asyncio
import asyncpg
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import app

# --------------------------
# Database URL fixture
# --------------------------
@pytest.fixture(scope="session")
def database_url():
    return "postgresql://postgres:postgres@localhost:5432/test_db"

# --------------------------
# Async DB setup coroutine
# --------------------------
async def setup_db(database_url: str):
    conn = await asyncpg.connect(database_url)
    try:
        # Create schema
        with open("migrations/001_create_sailings_table.up.sql", "r") as f:
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
    finally:
        await conn.close()


# --------------------------
# FastAPI TestClient fixture
# --------------------------
@pytest.fixture
def app_client(monkeypatch, database_url):
    monkeypatch.setenv("DATABASE_URL", database_url)

    # Run async DB setup synchronously
    asyncio.run(setup_db(database_url))

    with TestClient(app) as client:
        yield client
