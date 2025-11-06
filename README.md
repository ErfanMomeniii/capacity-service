# Capacity Service – China Main ↔ North Europe Main

## 📘 Table of Contents
- [Overview](#-Overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Dataset](#-dataset)
- [API Specification](#-api-specification)
- [SQL Query Logic](#-sql-query-logic)
- [Dockerized Setup](#-dockerized-setup)
- [Usage Guide](#-usage-guide)
- [Testing & Coverage](#-testing--coverage)
- [Observability](#-observability)
- [Future Enhancements](#-future-enhancements)
- [Contact](#-contact)

---

# 🧭 Overview

The **Capacity Service** is a high-performance, containerized API built to calculate **offered shipping capacity (TEU)** for the **China Main ↔ North Europe Main** corridor.  
It aggregates sailing-level data, computes weekly offered capacity, and provides a **4-week rolling average** for operational insights.

This service is engineered using **FastAPI**, **asyncpg**, and **Redis**, following **enterprise-grade design principles** emphasizing scalability, observability, and maintainability.

---

# ⚙️ Key Features

- **Weekly Capacity Computation** – Aggregates sailing-level TEU data per corridor and week.
- **4-Week Rolling Average** – Provides a short-term performance trend.
- **RESTful API** – `/capacity` endpoint with strong validation and OpenAPI documentation.
- **Caching Layer** – Optional Redis caching to reduce database load and accelerate responses.
- **Observability** – Structured logging, Prometheus metrics, and cache hit/miss counters.
- **Dockerized Deployment** – Complete stack setup with PostgreSQL, Redis, and migration support.

---

# 🧩 System Architecture

### 🔹 API Layer
- Exposes endpoints using FastAPI.
- Includes input validation, exception handling, and CORS middleware.

### 🔹 Service Layer (`CapacityService`)
- Implements business logic and caching.
- Manages data consistency and delegates repository queries.

### 🔹 Repository Layer (`CapacityRepository`)
- Executes optimized SQL queries for weekly aggregation and rolling averages.
- Provides fault-tolerant database access via `asyncpg`.

### 🔹 Database Layer (PostgreSQL)
- Stores sailing-level data for corridor capacity analytics.
- Handles deduplication, weekly aggregation, and rolling computation.

### 🔹 Cache Layer (Redis)
- Stores computed results with configurable TTL (default: 6 hours).
- Tracks performance metrics for cache usage and hits/misses.

---

# 🧾 Dataset

The service uses sailing-level data for the **China Main ↔ North Europe Main** corridor.

| Column                                     | Description                            |
| ------------------------------------------ | -------------------------------------- |
| `origin_at_utc`                            | Departure timestamp at origin port     |
| `origin_port_code`                         | Origin port code                       |
| `destination_port_code`                    | Destination port code                  |
| `service_version_and_roundtrip_identfiers` | Unique vessel-service identifier       |
| `origin_service_version_and_master`        | Origin service version identifier      |
| `destination_service_version_and_master`   | Destination service version identifier |
| `offered_capacity_teu`                     | Offered capacity in TEU                |

---

#  📡 API Specification
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

# 🧮 SQL Query Logic

The query handles:

- Deduplication of vessel-service-week combinations

- Weekly TEU aggregation

- 4-week rolling average computation

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

# 🐳 Dockerized Setup

The project uses Docker Compose for full-stack orchestration:

* app: FastAPI application

* db: PostgreSQL with health checks and persistent volume pgdata

* redis: Redis caching server with password protection

* migrate: Data loading/migration script executed before app startup

# 🚀 Usage Guide

### Start Services
```bash
docker-compose up --build
```

### Stop Services
```bash
docker-compose down
```

### Access API
```bash
curl "http://localhost:8000/capacity?date_from=2025-08-11&date_to=2025-08-25"
```

# 🧪 Testing & Coverage

The test suite validates:

- API responses and input validation

- Business logic and caching layer behavior

- SQL query correctness and aggregation

- Error handling and monitoring instrumentation

Run tests:
```bash
pytest --cov=app --cov-report=term-missing
```

## ✅ Coverage Summary

| Module                             | Coverage                                        |
| ---------------------------------- | ----------------------------------------------- |
| API & Middleware                   | **100%** (exception handlers, metrics, logging) |
| Repository Layer                   | **95%**                                         |
| Service Layer                      | **80%**                                         |
| Database Pool                      | **76%**                                         |
| Core Modules (Logging, Monitoring) | **100%**                                        |
| **Total**                          | **90%** overall coverage                        |

# 📈 Observability

* Structured Logging: Contextual logs per request.

* Prometheus Metrics: Cache hit/miss counters.

* Health checks: DB and Redis readiness checks via Docker Compose.

# 🔮 Future Enhancements

* Extend to multiple corridors.

* Add forecasting models for capacity prediction.

* Integrate Grafana dashboards for real-time observability.

# 👤 Contact

Erfan Momeni – erfamm5@gmail.com