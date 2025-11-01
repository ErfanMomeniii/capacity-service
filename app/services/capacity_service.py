from datetime import date
from typing import List, Dict
from fastapi import HTTPException
import asyncpg

from app.repositories.capacity_repository import CapacityRepository


class CapacityService:
    """Encapsulates business logic for offered capacity."""

    def __init__(self):
        self.repo = CapacityRepository()

    async def get_capacity_rolling_average(
        self, conn: asyncpg.Connection, start: date, end: date
    ) -> List[Dict]:
        if start > end:
            raise HTTPException(status_code=400, detail="date_from must be <= date_to")

        try:
            data = await self.repo.fetch_capacity(conn, start, end)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to fetch capacity: {exc}")

        # Could add post-processing logic here (filter, rename, etc.)
        return data
