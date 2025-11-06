from typing import List, Dict, Optional
from datetime import date
import asyncpg
from app.core.monitoring import monitor_query
from app.core import logging
from app.exceptions import CapacityDatabaseException

logger = logging.get_logger(__name__)


class CapacityRepository:
    """
    Repository layer responsible for fetching weekly capacity data from the database.

    Responsibilities:
    - Encapsulates SQL queries and DB access.
    - Provides monitoring hooks for query performance.
    - Handles errors gracefully, translating DB errors into service-specific exceptions.
    """

    def __init__(self):
        # Prepare commonly used SQL queries once to avoid repeated string parsing
        self._prepare_queries()

    def _prepare_queries(self) -> None:
        """
        Initializes the SQL query for retrieving weekly capacity with a 4-week rolling average.

        - Uses CTEs for intermediate aggregation.
        - Applies ROW_NUMBER() to deduplicate sailings per week per service.
        - Calculates a rolling 4-week average using a window function.
        """
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
            EXTRACT(WEEK FROM week_start_date)::int AS week_no,
            offered_capacity_teu,
            AVG(offered_capacity_teu) OVER (
                ORDER BY week_start_date
                ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
            )::integer AS offered_capacity_teu_4w_rolling_avg
        FROM weekly_capacity
        ORDER BY week_start_date;
        """

    # ------------------------------------------------------------
    # Core Repository Method
    # ------------------------------------------------------------
    @monitor_query("fetch_capacity")
    async def fetch_capacity(
            self,
            conn: asyncpg.Connection,
            start_date: date,
            end_date: date,
            corridor: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieves weekly capacity data within the specified date range.

        - Returns a list of dictionaries representing each week.
        - Decorated with a monitoring hook to track query performance.

        Raises:
            CapacityDatabaseException: For database errors or closed connections.
        """
        try:
            rows = await conn.fetch(self.capacity_query, start_date, end_date)
            # Convert asyncpg Record objects to plain dictionaries for downstream use
            return [dict(r) for r in rows]

        except Exception as e:
            # Structured logging for easier observability
            logger.error(
                "Database error while fetching capacity",
                extra={
                    "error_msg": str(e),
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "corridor": corridor
                }
            )

            # Map low-level DB errors to service-specific exception for API consistency
            if isinstance(e, (asyncpg.PostgresError, asyncpg.InterfaceError)) or "closed" in str(e).lower():
                raise CapacityDatabaseException(f"Database operation failed: {e}") from e

            # Reraise unexpected exceptions (could be programming errors)
            raise
