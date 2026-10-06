"""Ingestion-key authentication."""

from secrets import compare_digest
from typing import Annotated

from fastapi import Header

from app.core.config import get_settings
from app.core.errors import ApplicationError


def require_ingest_key(
    x_ingest_key: Annotated[str | None, Header(alias="X-Ingest-Key")] = None,
) -> None:
    expected = get_settings().INGEST_API_KEY.get_secret_value()
    if x_ingest_key is None or not compare_digest(x_ingest_key, expected):
        raise ApplicationError(
            status_code=401,
            code="INVALID_INGEST_KEY",
            message="Valid ingestion authentication is required.",
        )
