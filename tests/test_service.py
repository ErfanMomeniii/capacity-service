import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock
from app.services.capacity_service import CapacityService
from app.exceptions import CapacityValidationException, CapacityDatabaseException, CapacityUnexpectedException


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

        service = CapacityService()
        service.repo = mock_repo

        result = await service.get_capacity_rolling_average(
            conn=AsyncMock(),
            start=date(2024, 1, 1),
            end=date(2024, 3, 31)
        )

        assert len(result) == 1
        assert result[0]["offered_capacity_teu"] == 20000
        mock_repo.fetch_capacity.assert_called_once()

    async def test_get_capacity_validation(self):
        service = CapacityService()
        # start date > end date
        with pytest.raises(CapacityValidationException):
            await service.get_capacity_rolling_average(
                conn=AsyncMock(),
                start=date(2024, 3, 31),
                end=date(2024, 1, 1)
            )

    async def test_get_capacity_database_error(self):
        # Simulate DB error
        mock_repo = Mock()
        mock_repo.fetch_capacity = AsyncMock(side_effect=Exception("Database error"))

        service = CapacityService()
        service.repo = mock_repo  # Override repo

        with pytest.raises(CapacityDatabaseException) as exc_info:
            await service.get_capacity_rolling_average(
                conn=AsyncMock(),
                start=date(2024, 1, 1),
                end=date(2024, 3, 31)
            )
        assert "Database operation failed" in str(exc_info.value)

    async def test_get_capacity_unexpected_error(self):
        mock_repo = Mock()
        mock_repo.fetch_capacity = AsyncMock(side_effect=RuntimeError("Unexpected"))

        service = CapacityService()
        service.repo = mock_repo  # Override repo

        with pytest.raises(CapacityUnexpectedException) as exc_info:
            await service.get_capacity_rolling_average(
                conn=AsyncMock(),
                start=date(2024, 1, 1),
                end=date(2024, 3, 31)
            )
        assert "Unhandled server error" in str(exc_info.value)
