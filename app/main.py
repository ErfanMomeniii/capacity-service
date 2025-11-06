from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import os
from app.core import logging

from app.db.pool import init_db_pool, close_db_pool
from app.api.capacity import router as capacity_router
from app.exceptions import CapacityServiceException
from app.api.exception_handlers import (
    capacity_exception_handler,
    validation_exception_handler,
)
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.core.monitoring import router as monitoring_router

# Load environment variables early to configure logging and other dependencies
load_dotenv()

# Initialize logging with dynamic level control via environment variable
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.setup_logging(LOG_LEVEL)
logger = logging.get_logger(__name__)

# ------------------------------------------------------------
# FastAPI Application Setup
# ------------------------------------------------------------
app = FastAPI(
    title="Capacity Service",
    description="Compute 4-week rolling average offered capacity (TEU) per week.",
    version="1.0.0",
)

# ------------------------------------------------------------
# Global Exception Handlers
# ------------------------------------------------------------
# Register centralized exception handlers to ensure consistent API error responses
app.add_exception_handler(CapacityServiceException, capacity_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ------------------------------------------------------------
# Middleware Configuration
# ------------------------------------------------------------
# Enable CORS for external clients (temporary wildcard; should be scoped in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware for structured request logging and performance metrics
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)

# ------------------------------------------------------------
# Lifecycle Events
# ------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    """Initialize application resources such as DB connection pool."""
    logger.info("Starting app and initializing DB pool")
    await init_db_pool(app)
    logger.info("DB pool initialized")


@app.on_event("shutdown")
async def on_shutdown():
    """Gracefully close resources during application shutdown."""
    logger.info("Shutting down app and closing DB pool")
    await close_db_pool(app)
    logger.info("DB pool closed")

# ------------------------------------------------------------
# Health Check Endpoint
# ------------------------------------------------------------
@app.get("/health", tags=["health"])
async def health():
    """Lightweight health probe for container orchestration systems."""
    return {"status": "ok"}

# ------------------------------------------------------------
# Routers Registration
# ------------------------------------------------------------
# Monitoring routes expose metrics and system health insights
app.include_router(monitoring_router, prefix="", tags=["monitoring"])

# Business logic endpoints for capacity computation
app.include_router(capacity_router, prefix="", tags=["capacity"])
