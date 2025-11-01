from typing import List, Dict
import asyncpg
from pathlib import Path

SQL_FILE = Path(__file__).resolve().parents[2] / "queries" / "capacity_4w_rolling.sql"


class CapacityRepository:
    """Repository layer responsible for fetching capacity data."""

    def __init__(self):
        if not SQL_FILE.exists():
            raise RuntimeError(f"SQL file not found: {SQL_FILE}")
        self.sql = SQL_FILE.read_text(encoding="utf-8")

    async def fetch_capacity(
        self, conn: asyncpg.Connection, start_date, end_date
    ) -> List[Dict]:
        """Execute the SQL query for a given date range."""
        rows = await conn.fetch(self.sql, start_date, end_date)
        return [dict(r) for r in rows]
