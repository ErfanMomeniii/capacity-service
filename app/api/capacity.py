from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Annotated, List

import asyncpg
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from app.db.pool import get_conn
from app.services.capacity_service import CapacityService
from app.exceptions import (
    CapacityValidationException,
    CapacityDatabaseException,
    CapacityUnexpectedException,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Capacity"])


class CapacityRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    week_start_date: str
    week_no: int
    offered_capacity_teu: int
    offered_capacity_teu_4w_rolling_avg: int


@router.get("/capacity", response_model=List[CapacityRow])
async def get_capacity(
    date_from: Annotated[str, Query(..., regex=r"^\d{4}-\d{2}-\d{2}$")],
    date_to: Annotated[str, Query(..., regex=r"^\d{4}-\d{2}-\d{2}$")],
    conn: Annotated[asyncpg.Connection, Depends(get_conn)],
):
    """Returns weekly offered capacity and rolling averages."""

    try:
        start = datetime.strptime(date_from, "%Y-%m-%d").date()
        end = datetime.strptime(date_to, "%Y-%m-%d").date()
    except ValueError as exc:
        raise CapacityValidationException("Dates must be in format YYYY-MM-DD") from exc

    if start > end:
        raise CapacityValidationException("'date_from' must be <= 'date_to'")

    capacity_service = CapacityService()

    try:
        rows = await capacity_service.get_capacity_rolling_average(conn, start, end)
    except asyncpg.PostgresError as exc:
        raise CapacityDatabaseException("Database operation failed") from exc
    except Exception as exc:
        raise CapacityUnexpectedException("Unhandled server error") from exc

    return [
        CapacityRow(
            week_start_date=(
                r["week_start_date"].isoformat()
                if isinstance(r["week_start_date"], date)
                else str(r["week_start_date"])
            ),
            week_no=int(r["week_no"]),
            offered_capacity_teu=int(r["offered_capacity_teu"]),
            offered_capacity_teu_4w_rolling_avg=int(r["offered_capacity_teu_4w_rolling_avg"]),
        )
        for r in rows
    ]
