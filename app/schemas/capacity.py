from datetime import date, timedelta
from pydantic import BaseModel, validator, Field
from typing import Optional

from app.exceptions import DateRangeValidationError


class CapacityRequest(BaseModel):
    date_from: date = Field(..., description="Start date in YYYY-MM-DD format")
    date_to: date = Field(..., description="End date in YYYY-MM-DD format")
    corridor: Optional[str] = Field(
        default="china_main-north_europe_main",
        description="Trade corridor identifier"
    )

    @validator('date_to')
    def validate_date_range(cls, v, values):
        if 'date_from' in values:
            if v < values['date_from']:
                raise DateRangeValidationError("date_to must be after date_from")

            # Validate maximum date range (e.g., 1 year)
            max_range = timedelta(days=365)
            if v - values['date_from'] > max_range:
                raise DateRangeValidationError(
                    "Date range cannot exceed 1 year"
                )
        return v
