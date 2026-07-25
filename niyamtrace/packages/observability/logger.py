"""
packages/observability/logger.py — Structured Logging for NiyamTrace

Wraps Python's standard logging to provide structured JSON output for
production observability (log aggregation) and human-readable output
for development.

Supports contextvars for injecting `trace_id` into all log records
automatically during a request lifecycle.
"""

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

# Context variable to hold the current trace_id across async tasks/threads
current_trace_id: ContextVar[str] = ContextVar("current_trace_id", default="")


class StructuredFormatter(logging.Formatter):
    """Formats log records as JSON with trace_id correlation."""
    
    def format(self, record: logging.LogRecord) -> str:
        trace_id = current_trace_id.get()
        
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if trace_id:
            log_obj["trace_id"] = trace_id
            
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


def get_logger(name: str) -> logging.Logger:
    """Get a structured logger configured based on environment."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if get_logger is called multiple times
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(os.environ.get("NIYAMTRACE_LOG_LEVEL", "INFO").upper())
    
    handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatting if in production (or if requested)
    if os.environ.get("LOG_FORMAT", "").lower() == "json":
        handler.setFormatter(StructuredFormatter())
    else:
        # Development human-readable format
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s (trace=%(trace_id)s): %(message)s"
            )
        )
        
        # Inject trace_id into the LogRecord for the dev formatter
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.trace_id = current_trace_id.get() or "-"
            return record
        logging.setLogRecordFactory(record_factory)

    logger.addHandler(handler)
    logger.propagate = False
    return logger
