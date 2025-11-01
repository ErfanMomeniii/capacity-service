-- queries/capacity_4w_rolling.sql
-- Params:
--   $1 => start_date (DATE), e.g. '2024-01-01'
--   $2 => end_date   (DATE), e.g. '2024-03-31'

WITH filtered AS (
    SELECT
        service_version_and_roundtrip_identfiers,
        origin_service_version_and_master,
        destination_service_version_and_master,
        vessel_identifier,
        origin_at_utc,
        offered_capacity_teu,
        origin_port_code,
        destination_port_code
    FROM sailings
    WHERE origin_service_version_and_master = 'china_main'
      AND destination_service_version_and_master = 'north_europe_main'
      AND origin_at_utc::date >= ($1::date - INTERVAL '21 days')
      AND origin_at_utc::date <= ($2::date)
),
latest_origin_per_journey AS (
    SELECT DISTINCT ON (
        service_version_and_roundtrip_identfiers,
        origin_service_version_and_master,
        destination_service_version_and_master,
        vessel_identifier
    )
        service_version_and_roundtrip_identfiers,
        origin_service_version_and_master,
        destination_service_version_and_master,
        vessel_identifier,
        origin_at_utc,
        offered_capacity_teu
    FROM filtered
    ORDER BY
        service_version_and_roundtrip_identfiers,
        origin_service_version_and_master,
        destination_service_version_and_master,
        vessel_identifier,
        origin_at_utc DESC
),
weekly_sum AS (
    SELECT
        date_trunc('week', origin_at_utc::date)::date AS week_start_date,
        extract('week' from origin_at_utc::date)::int AS week_no,
        SUM(offered_capacity_teu) AS offered_capacity_teu
    FROM latest_origin_per_journey
    WHERE origin_at_utc::date >= $1::date
      AND origin_at_utc::date <= $2::date
    GROUP BY date_trunc('week', origin_at_utc::date)
),
rolling_avg AS (
    SELECT
        week_start_date,
        week_no,
        offered_capacity_teu,
        ROUND(AVG(offered_capacity_teu) OVER (
            ORDER BY week_start_date
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ))::bigint AS offered_capacity_teu_4w_rolling_avg
    FROM weekly_sum
)
SELECT
    to_char(week_start_date, 'YYYY-MM-DD') AS week_start_date,
    week_no,
    offered_capacity_teu,
    offered_capacity_teu_4w_rolling_avg
FROM rolling_avg
ORDER BY week_start_date;
