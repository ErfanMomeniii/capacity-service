class CapacityServiceException(Exception):
    """Base exception for capacity service"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class DateRangeValidationError(CapacityServiceException):
    """Raised when date range is invalid"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class CapacityCalculationError(CapacityServiceException):
    """Raised when capacity calculation fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)