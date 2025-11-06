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

load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.setup_logging(LOG_LEVEL)

logger = logging.get_logger("capacity-service")

app = FastAPI(
    title="Capacity Service",
    description="Compute 4-week rolling average offered capacity (TEU) per week.",
    version="1.0.0",
)

app.add_exception_handler(CapacityServiceException, capacity_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)


@app.on_event("startup")
async def on_startup():
    logger.info("Starting app and initializing DB pool")
    await init_db_pool(app)
    logger.info("DB pool initialized")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down app and closing DB pool")
    await close_db_pool(app)
    logger.info("DB pool closed")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


app.include_router(monitoring_router, prefix="", tags=["monitoring"])

app.include_router(capacity_router, prefix="", tags=["capacity"])
