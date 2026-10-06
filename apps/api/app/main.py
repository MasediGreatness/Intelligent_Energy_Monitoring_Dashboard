"""FastAPI application entry point."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

from app.api.health import router as health_router
from app.api.readiness import router as readiness_router
from app.api.v1.auth import router as auth_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.live import router as live_router
from app.api.v1.protected_writes import router as protected_writes_router
from app.api.v1.read import router as read_router
from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import request_context_middleware
from app.core.rate_limit import limiter, rate_limit_error
from app.services.live import live_manager

configure_logging()
get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    heartbeat = asyncio.create_task(live_manager.heartbeat_forever())
    try:
        yield
    finally:
        heartbeat.cancel()
        await live_manager.reset_for_test()


app = FastAPI(
    title="Intelligent Industrial Energy Dashboard API",
    version="0.1.0",
    description="Monitoring and advisory only; no industrial load-control path.",
    lifespan=lifespan,
)
app.middleware("http")(request_context_middleware)
install_error_handlers(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_error)  # type: ignore[arg-type]
app.include_router(health_router)
app.include_router(readiness_router)
app.include_router(ingestion_router)
app.include_router(read_router)
app.include_router(auth_router)
app.include_router(protected_writes_router)
app.include_router(live_router)
