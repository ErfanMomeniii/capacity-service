import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock
from app.services.capacity_service import CapacityService
from app.exceptions import CapacityServiceException


@pytest.mark.asyncio
class TestCapacityService:
    async def test_get_capacity_success(self):
        mock_repo = Mock()
        mock_repo.fetch_capacity = AsyncMock()
        mock_repo.fetch_capacity.return_value = [
            {
                "week_start_date": date(2024, 1, 1),
                "week_no": 1,
                "offered_capacity_teu": 20000,
                "offered_capacity_teu_4w_rolling_avg": 21000
            }
        ]

        service = CapacityService(repository=mock_repo)
        result = await service.get_capacity(
            conn=AsyncMock(),
            date_from=date(2024, 1, 1),
            date_to=date(2024, 3, 31)
        )

        assert len(result) == 1
        assert result[0]["offered_capacity_teu"] == 20000
        mock_repo.fetch_capacity.assert_called_once()

    async def test_get_capacity_validation(self):
        service = CapacityService()
        with pytest.raises(ValueError):
            await service.get_capacity(
                conn=AsyncMock(),
                date_from=date(2024, 3, 31),
                date_to=date(2024, 1, 1)
            )

    async def test_get_capacity_error_handling(self):
        mock_repo = Mock()
        mock_repo.fetch_capacity = AsyncMock(side_effect=Exception("Database error"))

        service = CapacityService(repository=mock_repo)
        with pytest.raises(CapacityServiceException):
            await service.get_capacity(
                conn=AsyncMock(),
                date_from=date(2024, 1, 1),
                date_to=date(2024, 3, 31)
            )