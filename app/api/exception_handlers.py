import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.exceptions import CapacityServiceException

logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Custom Exception Handlers
# ------------------------------------------------------------
async def capacity_exception_handler(
    request: Request,
    exc: CapacityServiceException
) -> JSONResponse:
    """
    Handles all CapacityServiceException instances.

    Responsibilities:
    - Logs the error with structured fields for observability.
    - Returns a standardized JSON payload including error type, message, and status code.
    - Ensures consistent API error responses across the service.
    """
    logger.error(
        f"[{exc.__class__.__name__}] {exc.message}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handles FastAPI request validation errors (e.g., invalid query parameters or payloads).

    Responsibilities:
    - Logs validation errors at WARNING level with structured details.
    - Returns standardized JSON with error type, detailed validation errors, and HTTP 422 status.
    - Provides clients with actionable feedback while maintaining consistent error format.
    """
    logger.warning(
        "Validation error",
        extra={
            "errors": exc.errors(),
            "body": getattr(exc, "body", None),
            "path": str(request.url.path),
        },
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "details": exc.errors(),
            "status_code": 422,
        },
    )
