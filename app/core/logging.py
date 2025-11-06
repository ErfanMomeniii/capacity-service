import logging
import json
import sys
from datetime import datetime


# ------------------------------------------------------------
# JSON Logging Formatter
# ------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Features:
    - Converts log records to JSON with timestamp, level, logger, and message.
    - Includes user-defined `extra` fields while excluding irrelevant internal attributes.
    - Designed for structured logging pipelines and observability dashboards.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Exclude internal fields that are not relevant for structured logging
        exclude_keys = {
            "args", "msg", "exc_info", "exc_text", "stack_info",
            "lineno", "pathname", "filename", "module", "funcName",
            "created", "msecs", "relativeCreated", "thread",
            "threadName", "processName", "process", "taskName",
            "color_message",
        }

        # Include custom extra fields from log record
        for key, value in record.__dict__.items():
            if key not in log_record and key not in exclude_keys:
                log_record[key] = value

        return json.dumps(log_record, ensure_ascii=False)


# ------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------
def setup_logging(level: str = "INFO"):
    """
    Configure global JSON logging for the application.

    Responsibilities:
    - Sets up a single structured logging pipeline for Uvicorn, FastAPI, and the application.
    - Ensures logs are emitted in JSON for observability, monitoring, and correlation.
    - Overrides default handlers to prevent mixed log formats.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Align Uvicorn/FastAPI logs with same JSON format
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        log = logging.getLogger(name)
        log.handlers.clear()
        log.addHandler(handler)
        log.setLevel(level)
        log.propagate = False

    # Configure dedicated app logger
    app_logger = logging.getLogger("capacity-service")
    app_logger.setLevel(level)
    app_logger.propagate = False
    app_logger.addHandler(handler)


def get_logger(name: str):
    """
    Returns a structured JSON logger instance for the given name.

    - Useful for per-module logging with consistent formatting.
    - Prevents duplicate logs via `propagate = False`.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
