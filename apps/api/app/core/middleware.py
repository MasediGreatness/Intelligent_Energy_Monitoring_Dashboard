"""HTTP middleware shared by all routes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

import structlog
from fastapi import Request, Response

from app.core.logging import get_logger


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach a request ID and emit one structured completion record."""

    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    started = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        get_logger().exception(
            "request_failed",
            method=request.method,
            path=request.url.path,
            duration_ms=round((perf_counter() - started) * 1000, 2),
        )
        raise

    response.headers["X-Request-ID"] = request_id
    get_logger().info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round((perf_counter() - started) * 1000, 2),
    )
    return response
