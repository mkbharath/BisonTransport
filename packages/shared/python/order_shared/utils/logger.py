"""Structured JSON logger with context injection and PII masking."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from order_shared.utils.pii_masker import mask_pii

# Context variables for structured logging
_run_id: ContextVar[str | None] = ContextVar("run_id", default=None)
_email_id: ContextVar[str | None] = ContextVar("email_id", default=None)
_order_id: ContextVar[str | None] = ContextVar("order_id", default=None)
_agent_type: ContextVar[str | None] = ContextVar("agent_type", default=None)


def set_log_context(
    run_id: str | UUID | None = None,
    email_id: str | UUID | None = None,
    order_id: str | UUID | None = None,
    agent_type: str | None = None,
) -> None:
    """Set context variables for structured logging."""
    if run_id:
        _run_id.set(str(run_id))
    if email_id:
        _email_id.set(str(email_id))
    if order_id:
        _order_id.set(str(order_id))
    if agent_type:
        _agent_type.set(agent_type)


def clear_log_context() -> None:
    """Clear all logging context variables."""
    _run_id.set(None)
    _email_id.set(None)
    _order_id.set(None)
    _agent_type.set(None)


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as JSON with context injection and PII masking."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_pii(record.getMessage()),
        }

        # Inject context variables
        if _run_id.get():
            log_entry["run_id"] = _run_id.get()
        if _email_id.get():
            log_entry["email_id"] = _email_id.get()
        if _order_id.get():
            log_entry["order_id"] = _order_id.get()
        if _agent_type.get():
            log_entry["agent_type"] = _agent_type.get()

        # Include exception info if present
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields
        for key in ("duration_ms", "status", "action", "tokens_in", "tokens_out"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry)


def get_logger(name: str) -> logging.Logger:
    """Get a structured JSON logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("Processing email", extra={"duration_ms": 150})
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
