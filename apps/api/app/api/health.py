"""Process health routes."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return process liveness without touching the database."""

    return HealthResponse(status="ok", service="energy-dashboard-api", version="0.1.0")
