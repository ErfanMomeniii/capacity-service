# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.db import init_db_pool, close_db_pool
from app.api.capacity import router as capacity_router

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("capacity-service")

app = FastAPI(
    title="Capacity Service",
    description="Compute 4-week rolling average offered capacity (TEU) per week.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


app.include_router(capacity_router, prefix="", tags=["capacity"])
