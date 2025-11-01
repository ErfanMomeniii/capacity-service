from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.exceptions import CapacityServiceException
import logging

logger = logging.getLogger(__name__)

async def capacity_exception_handler(
    request: Request,
    exc: CapacityServiceException
) -> JSONResponse:
    logger.error(f"CapacityService error: {exc.message}",
                 extra={
                     "path": request.url.path,
                     "method": request.method,
                     "status_code": exc.status_code
                 })
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code
        }
    )

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    logger.error("Validation error",
                 extra={
                     "errors": exc.errors(),
                     "body": exc.body,
                     "path": request.url.path
                 })
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "details": exc.errors(),
            "status_code": 422
        }
    )