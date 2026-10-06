from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Engine

from app.db.session import get_engine
from app.schemas.readiness import ReadinessResponse
from app.services.readiness import check_readiness

router = APIRouter(tags=["health"])


@router.get("/ready", response_model=ReadinessResponse)
def readiness(engine: Annotated[Engine, Depends(get_engine)]) -> ReadinessResponse:
    return check_readiness(engine)
