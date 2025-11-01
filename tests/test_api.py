import pytest

@pytest.mark.asyncio
async def test_capacity_endpoint(app_client):
    resp = await app_client.get("/capacity?date_from=2024-01-01&date_to=2024-03-31")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    first = data[0]
    assert "week_start_date" in first
    assert "week_no" in first
    assert "offered_capacity_teu" in first
    assert "offered_capacity_teu_4w_rolling_avg" in first

    assert isinstance(first["week_start_date"], str)
