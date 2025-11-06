import pytest
from datetime import date, timedelta
from fastapi import FastAPI


class TestCapacityAPI:
    def test_capacity_endpoint_success(self, app_client):
        response = app_client.get("/capacity?date_from=2024-01-01&date_to=2024-03-31")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        first_item = data[0]
        assert all(key in first_item for key in [
            "week_start_date",
            "week_no",
            "offered_capacity_teu",
            "offered_capacity_teu_4w_rolling_avg"
        ])

    def test_capacity_endpoint_invalid_dates(self, app_client):
        response = app_client.get("/capacity?date_from=2024-13-01&date_to=2024-03-31")
        assert response.status_code == 400

        response = app_client.get("/capacity?date_from=2024-01-01&date_to=invalid")
        assert response.status_code == 422

    def test_capacity_endpoint_missing_params(self, app_client):
        response = app_client.get("/capacity?date_from=2024-01-01")
        assert response.status_code == 422

        response = app_client.get("/capacity?date_to=2024-03-31")
        assert response.status_code == 422

    def test_capacity_endpoint_date_range_validation(self, app_client):
        response = app_client.get(
            "/capacity?date_from=2024-03-31&date_to=2024-01-01"
        )
        assert response.status_code == 400

    def test_capacity_endpoint_future_dates(self, app_client):
        future_date = date.today() + timedelta(days=365)
        response = app_client.get(
            f"/capacity?date_from={future_date}&date_to={future_date + timedelta(days=90)}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_metrics_endpoint_exposes_data(self, app_client):
        """Ensure /metrics returns Prometheus metrics output."""
        response = app_client.get("/metrics")
        assert response.status_code == 200
        assert "capacity_request_total" in response.text
