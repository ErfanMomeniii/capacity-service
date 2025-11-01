import os
import asyncio
import asyncpg
import pytest
import pathlib
from httpx import AsyncClient
from app.main import app as fastapi_app

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]

SAMPLE_ROWS = [
    (
        "SRV001", "china_main", "north_europe_main", "VSL001", "CNSHA", "NLRTM",
        "2024-01-03 08:00:00+00", 20000
    ),
    (
        "SRV001", "china_main", "north_europe_main", "VSL001", "CNYTN", "NLRTM",
        "2024-01-10 08:00:00+00", 18000
    ),
    (
        "SRV002", "china_main", "north_europe_main", "VSL002", "CNSHA", "NLAMS",
        "2024-01-17 08:00:00+00", 23000
    ),
    (
        "SRV002", "china_main", "north_europe_main", "VSL002", "CNSHA", "NLAMS",
        "2024-02-01 08:00:00+00", 22000
    ),
    (
        "SRV003", "china_main", "north_europe_main", "VSL003", "CNSHA", "DEHAM",
        "2024-02-14 08:00:00+00", 25000
    ),
    (
        "SRV003", "china_main", "north_europe_main", "VSL003", "CNSHA", "DEHAM",
        "2024-02-21 08:00:00+00", 26000
    ),
    (
        "SRV004", "china_main", "north_europe_main", "VSL004", "CNSHA", "GBFXT",
        "2024-03-05 08:00:00+00", 19000
    ),
    (
        "SRV005", "china_main", "north_europe_main", "VSL005", "CNYTN", "FRLEH",
        "2024-03-19 08:00:00+00", 21000
    ),
]


@pytest.fixture(scope="session")
def database_url():
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Please set TEST_DATABASE_URL or DATABASE_URL for tests")
    return url


@pytest.fixture(scope="session")
async def init_db(database_url):
    """
    Create schema and load sample rows for tests.
    """
    conn = await asyncpg.connect(database_url)
    try:
        schema_path = BASE_DIR / "db" / "schema.sql"
        schema_sql = schema_path.read_text(encoding="utf-8")
        # run schema (drop/create)
        await conn.execute(schema_sql)

        insert_sql = """
        INSERT INTO sailings(
            service_version_and_roundtrip_identfiers,
            origin_service_version_and_master,
            destination_service_version_and_master,
            vessel_identifier,
            origin_port_code,
            destination_port_code,
            origin_at_utc,
            offered_capacity_teu
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        """

        # Insert sample rows
        for row in SAMPLE_ROWS:
            await conn.execute(insert_sql, *row)

        yield  # tests run here

    finally:
        await conn.close()


@pytest.fixture
async def app_client(init_db, database_url):
    """
    Provide an AsyncClient for FastAPI app. Sets TEST_DATABASE_URL in env
    before app startup so the app will connect to the test database.
    """
    # ensure FastAPI reads correct DB url during startup
    os.environ["DATABASE_URL"] = database_url

    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        yield ac
