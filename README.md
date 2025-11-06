# Capacity Service – China Main ↔ North Europe Main
## Overview

Capacity Service is a high-performance, containerized API designed to compute offered shipping capacity (TEU) on the China Main ↔ North Europe Main corridor. It aggregates sailing-level raw data, calculates weekly offered capacity, and provides a 4-week rolling average.

The service is built with FastAPI, asyncpg, and Redis caching, following enterprise-grade patterns for scalability, observability, and maintainability.

## Features

* Weekly Capacity Computation: Aggregates sailing-level TEU data per corridor and week.

* 4-Week Rolling Average: Provides rolling average to track short-term trends.

* RESTful API: /capacity endpoint with proper input validation and OpenAPI docs.

* Caching Layer: Optional Redis caching to reduce database load and improve performance.

* Observability: Structured logging, request metrics, and Prometheus counters for cache hits/misses.

* Dockerized Deployment: Full container orchestration with PostgreSQL, Redis, and migration scripts.


## Architecture
### Components

* API Layer

  * FastAPI endpoints with exception handling and input validation.

  * Middleware for logging, metrics, and CORS handling.

* Service Layer (CapacityService)

  * Handles business logic, Redis caching, and delegating queries to the repository.

  * Ensures data consistency and validation.

* Repository Layer (CapacityRepository)

  * Executes SQL queries for weekly capacity with deduplication and rolling averages.

  * Includes monitoring, robust error handling, and asynchronous PostgreSQL access.

* Database Layer (PostgreSQL)

  * Stores sailing-level data.

  * SQL query computes:

    * Weekly aggregation per corridor

    * Deduplication of vessel-service-week combinations

    * 4-week rolling average

* Cache Layer (Redis)

  * Stores query results for configurable TTL (default 6 hours).

  * Tracks cache hits/misses for observability.

## Dataset

The dataset contains sailing-level information for China Main ↔ North Europe Main. Key columns:

| Column                                     | Description                            |
| ------------------------------------------ | -------------------------------------- |
| `origin_at_utc`                            | Departure timestamp at origin port     |
| `origin_port_code`                         | Origin port code                       |
| `destination_port_code`                    | Destination port code                  |
| `service_version_and_roundtrip_identfiers` | Unique vessel-service identifier       |
| `origin_service_version_and_master`        | Origin service version identifier      |
| `destination_service_version_and_master`   | Destination service version identifier |
| `offered_capacity_teu`                     | Offered capacity in TEU                |

## API Specification
### Health Check
```
GET /health
```

Response
```
{"status": "ok"}
```

### Capacity Endpoint
```
GET /capacity?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
```

Parameters

| Name      | Type   | Description             |
| --------- | ------ | ----------------------- |
| date_from | string | Start date (YYYY-MM-DD) |
| date_to   | string | End date (YYYY-MM-DD)   |


Response Example
```
[
    {
        "week_start_date": "2025-08-11",
        "week_no": 33,
        "offered_capacity_teu": 123000,
        "offered_capacity_teu_4w_rolling_avg": 118000
    },
    {
        "week_start_date": "2025-08-18",
        "week_no": 34,
        "offered_capacity_teu": 123000,
        "offered_capacity_teu_4w_rolling_avg": 122000
    },
    {
        "week_start_date": "2025-08-25",
        "week_no": 35,
        "offered_capacity_teu": 86000,
        "offered_capacity_teu_4w_rolling_avg": 112000
    }
]
```

## SQL Query Overview

The query handles:

* Deduplication of vessel-service-week combinations

* Weekly TEU aggregation

* 4-week rolling average computation

```sql
WITH base AS (
    SELECT 
        date_trunc('week', origin_at_utc) AS week_start_date,
        offered_capacity_teu,
        ROW_NUMBER() OVER (
            PARTITION BY service_version_and_roundtrip_identfiers,
                         origin_service_version_and_master,
                         destination_service_version_and_master
            ORDER BY origin_at_utc DESC
        ) AS rn
    FROM sailings
    WHERE origin = 'china_main'
      AND destination = 'north_europe_main'
      AND origin_at_utc BETWEEN $1 AND $2
),
weekly_capacity AS (
    SELECT week_start_date, SUM(offered_capacity_teu) AS offered_capacity_teu
    FROM base
    WHERE rn = 1
    GROUP BY week_start_date
)
SELECT 
    week_start_date::date,
    EXTRACT(WEEK FROM week_start_date)::int AS week_no,
    offered_capacity_teu,
    AVG(offered_capacity_teu) OVER (
        ORDER BY week_start_date
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    )::int AS offered_capacity_teu_4w_rolling_avg
FROM weekly_capacity
ORDER BY week_start_date;
```