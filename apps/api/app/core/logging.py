"""Structured logging configuration."""

from __future__ import annotations

import logging
from typing import cast

import structlog


def configure_logging() -> None:
    """Configure standard-library and application logs as JSON."""

    logging.basicConfig(format="%(message)s", level=logging.INFO, force=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.stdlib.BoundLogger:
    """Return the application logger."""

    return cast(
        structlog.stdlib.BoundLogger,
        structlog.get_logger("energy_dashboard.api"),
    )
