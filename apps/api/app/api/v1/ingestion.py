from typing import Annotated

from anyio import from_thread
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.ingest_auth import require_ingest_key
from app.core.rate_limit import limiter
from app.db.session import get_db_session
from app.schemas.ingestion import MeasurementIngestBatch, MeasurementIngestResponse
from app.services.ingestion import ingest_measurements
from app.services.live import publish_committed_measurements

router = APIRouter(prefix="/api/v1/ingest", tags=["ingestion"])


@router.post(
    "/measurements",
    response_model=MeasurementIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_ingest_key)],
)
@limiter.limit("120/minute")
def ingest_measurement_batch(
    request: Request,
    batch: MeasurementIngestBatch,
    session: Annotated[Session, Depends(get_db_session)],
) -> MeasurementIngestResponse:
    return ingest_measurements(
        session,
        batch,
        on_committed=lambda items: from_thread.run(
            publish_committed_measurements, items
        ),
    )
