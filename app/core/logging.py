import logging
import json
import sys
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra structured fields but exclude irrelevant internals
        exclude_keys = {
            "args", "msg", "exc_info", "exc_text", "stack_info",
            "lineno", "pathname", "filename", "module", "funcName",
            "created", "msecs", "relativeCreated", "thread",
            "threadName", "processName", "process", "taskName",
            "color_message",
        }

        for key, value in record.__dict__.items():
            if key not in log_record and key not in exclude_keys:
                log_record[key] = value

        return json.dumps(log_record, ensure_ascii=False)


def setup_logging(level: str = "INFO"):
    """
    Configures a single JSON logging pipeline for Uvicorn, FastAPI, and the app.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Align Uvicorn/FastAPI logs to use the same JSON format
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        log = logging.getLogger(name)
        log.handlers.clear()
        log.addHandler(handler)
        log.setLevel(level)
        log.propagate = False

    # Application main logger
    app_logger = logging.getLogger("capacity-service")
    app_logger.setLevel(level)
    app_logger.propagate = False
    app_logger.addHandler(handler)

def get_logger(name: str):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger