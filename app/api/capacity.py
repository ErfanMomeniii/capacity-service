# app/api/capacity.py
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List
from datetime import datetime
from pathlib import Path
import logging

from app.db import get_conn
import asyncpg

logger = logging.getLogger("capacity-service.capacity")

router = APIRouter()


class CapacityRow(BaseModel):
    week_start_date: str
    week_no: int
    offered_capacity_teu: int
    offered_capacity_teu_4w_rolling_avg: int


SQL_PATH = Path(__file__).resolve().parents[3] / "queries" / "capacity_4w_rolling.sql"
if not SQL_PATH.exists():
    raise RuntimeError(f"Missing SQL file: {SQL_PATH}")

SQL_QUERY = SQL_PATH.read_text(encoding="utf-8")


@router.get("/capacity", response_model=List[CapacityRow])
async def get_capacity(
    date_from: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$"),
    date_to: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$"),
    conn: asyncpg.Connection = Depends(get_conn),
):
    """
    Returns weekly offered capacity and 4-week rolling average for the
    china_main -> north_europe_main corridor.

    Query params:
      - date_from: YYYY-MM-DD
      - date_to:   YYYY-MM-DD
    """
    try:
        start = datetime.strptime(date_from, "%Y-%m-%d").date()
        end = datetime.strptime(date_to, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in format YYYY-MM-DD")

    if start > end:
        raise HTTPException(status_code=400, detail="date_from must be <= date_to")

    try:
        rows = await conn.fetch(SQL_QUERY, start, end)
    except Exception as exc:
        logger.exception("Database query failed")
        raise HTTPException(status_code=500, detail="Database query failed") from exc

    result = []
    for r in rows:
        result.append(
            {
                "week_start_date": r["week_start_date"],
                "week_no": int(r["week_no"]),
                "offered_capacity_teu": int(r["offered_capacity_teu"]),
                "offered_capacity_teu_4w_rolling_avg": int(r["offered_capacity_teu_4w_rolling_avg"]),
            }
        )

    return result
