import pytest
import asyncpg
from datetime import date


@pytest.mark.usefixtures("app_client")
class TestIntegration:

    def test_full_capacity_flow(self, app_client):
        # Query the endpoint
        response = app_client.get("/capacity?date_from=2024-01-01&date_to=2024-03-31")
        assert response.status_code == 200
        data = response.json()

        assert len(data) > 0

        # Check all dates are within range
        start_date = date.fromisoformat("2024-01-01")
        end_date = date.fromisoformat("2024-03-31")
        assert all(
            start_date <= date.fromisoformat(item["week_start_date"]) <= end_date
            for item in data
        )

        # Check rolling average
        for i, item in enumerate(data):
            if i >= 3:  # rolling average requires at least 4 weeks
                assert item["offered_capacity_teu_4w_rolling_avg"] is not None

        # Check data integrity
        assert all(
            isinstance(item["offered_capacity_teu"], (int, float)) and
            item["offered_capacity_teu"] > 0
            for item in data
        )

    def test_database_connection_handling(self, app_client):
        # Run multiple requests to simulate concurrency
        responses = [app_client.get("/capacity?date_from=2024-01-01&date_to=2024-03-31") for _ in range(5)]
        assert all(response.status_code == 200 for response in responses)
