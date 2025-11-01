from typing import List, Dict, Optional
from datetime import date
import asyncpg
from app.db.metrics import monitor_query

class CapacityRepository:
    def __init__(self):
        self._prepare_queries()

    def _prepare_queries(self) -> None:
        self.capacity_query = """
        WITH weekly_capacity AS (
            SELECT 
                date_trunc('week', origin_at_utc) as week_start_date,
                MAX(offered_capacity_teu) as offered_capacity_teu,
                ROW_NUMBER() OVER (
                    PARTITION BY 
                        service_version_and_roundtrip_identfiers,
                        origin_service_version_and_master,
                        destination_service_version_and_master
                    ORDER BY origin_at_utc DESC
                ) as rn
            FROM sailings
            WHERE 
                origin_service_version_and_master = 'china_main'
                AND destination_service_version_and_master = 'north_europe_main'
                AND origin_at_utc BETWEEN $1 AND $2
            GROUP BY 
                week_start_date,
                service_version_and_roundtrip_identfiers,
                origin_service_version_and_master,
                destination_service_version_and_master
            HAVING rn = 1
        )
        SELECT 
            week_start_date::date as week_start_date,
            EXTRACT(WEEK FROM week_start_date) as week_no,
            SUM(offered_capacity_teu) as offered_capacity_teu,
            AVG(SUM(offered_capacity_teu)) OVER (
                ORDER BY week_start_date
                ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
            )::integer as offered_capacity_teu_4w_rolling_avg
        FROM weekly_capacity
        GROUP BY week_start_date
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
            raise