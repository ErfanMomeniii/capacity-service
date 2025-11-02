from typing import List, Dict, Optional
from datetime import date
import asyncpg
from app.db.metrics import monitor_query
from app.core import logging
from app.exceptions import CapacityDatabaseException

logger = logging.get_logger(__name__)

class CapacityRepository:
    def __init__(self):
        self._prepare_queries()

    def _prepare_queries(self) -> None:
        self.capacity_query = """
        WITH base AS (
    SELECT 
        date_trunc('week', origin_at_utc) AS week_start_date,
        offered_capacity_teu,
        ROW_NUMBER() OVER (
            PARTITION BY 
                service_version_and_roundtrip_identfiers,
                origin_service_version_and_master,
                destination_service_version_and_master
            ORDER BY origin_at_utc DESC
        ) AS rn
    FROM sailings
    WHERE 
    origin = 'china_main'
    AND destination = 'north_europe_main'
    AND origin_at_utc BETWEEN $1 AND $2
),
weekly_capacity AS (
    SELECT 
        week_start_date,
        SUM(offered_capacity_teu) AS offered_capacity_teu
    FROM base
    WHERE rn = 1
    GROUP BY week_start_date
)
SELECT 
    week_start_date::date AS week_start_date,
    EXTRACT(WEEK FROM week_start_date) AS week_no,
    offered_capacity_teu,
    AVG(offered_capacity_teu) OVER (
        ORDER BY week_start_date
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    )::integer AS offered_capacity_teu_4w_rolling_avg
FROM weekly_capacity
ORDER BY week_start_date;
        """

    @monitor_query("fetch_capacity")
    async def fetch_capacity(
        self,
        conn: asyncpg.Connection,
        start_date: date,
        end_date: date,
        corridor: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch capacity data with optimized query and monitoring.
        """
        try:
            rows = await conn.fetch(
                self.capacity_query,
                start_date,
                end_date
            )
            return [dict(r) for r in rows]
        except asyncpg.PostgresError as e:
            logger.error(
                "Database error while fetching capacity",
                extra={
                    "error": str(e),
                    "start_date": start_date,
                    "end_date": end_date,
                    "corridor": corridor
                }
            )

            if isinstance(e, (ConnectionError, OSError)) or "closed" in str(e).lower():
                raise CapacityDatabaseException(str(e)) from e
            import asyncpg
            if isinstance(e, asyncpg.InterfaceError):
                raise CapacityDatabaseException(str(e)) from e

            raise