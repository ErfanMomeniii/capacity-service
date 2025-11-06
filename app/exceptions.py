from fastapi import status


# ------------------------------------------------------------
# Base Exception Hierarchy
# ------------------------------------------------------------
# This hierarchy standardizes error handling across the Capacity Service.
# Each subclass represents a specific operational domain (validation, DB, etc.),
# allowing consistent response formatting and easier exception-based control flow.

class CapacityServiceException(Exception):
    """Base exception for all capacity service errors.

    Each custom exception inherits from this class to ensure
    a consistent interface for error message and HTTP status code.
    """

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ------------------------------------------------------------
# Domain-Specific Exceptions
# ------------------------------------------------------------
class CapacityValidationException(CapacityServiceException):
    """Raised when client-provided input or query parameters are invalid.

    Typically triggered during request validation or data preprocessing
    before computation or database access.
    """

    def __init__(self, message: str = "Invalid input data"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class CapacityDatabaseException(CapacityServiceException):
    """Raised when a database-related operation fails.

    Used to abstract away lower-level database errors
    (e.g., connection timeouts, constraint violations) into HTTP-friendly responses.
    """

    def __init__(self, message: str = "Database query failed"):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY)


class CapacityUnexpectedException(CapacityServiceException):
    """Raised for unhandled or unexpected internal service errors.

    Catch-all category to avoid leaking raw Python exceptions to clients,
    preserving API stability and observability through structured logging.
    """

    def __init__(self, message: str = "Unexpected internal error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)
