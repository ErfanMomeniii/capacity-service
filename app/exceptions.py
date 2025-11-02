from fastapi import status


class CapacityServiceException(Exception):
    """Base exception for all capacity service errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CapacityValidationException(CapacityServiceException):
    """Raised when invalid query parameters or inputs are detected."""

    def __init__(self, message: str = "Invalid input data"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class CapacityDatabaseException(CapacityServiceException):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database query failed"):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY)


class CapacityUnexpectedException(CapacityServiceException):
    """Raised for unknown or unhandled internal errors."""

    def __init__(self, message: str = "Unexpected internal error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)
