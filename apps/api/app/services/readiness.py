from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.errors import ApplicationError
from app.schemas.readiness import ReadinessResponse


def check_readiness(engine: Engine) -> ReadinessResponse:
    try:
        with engine.connect() as connection:
            current = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise ApplicationError(
            status_code=503,
            code="DATABASE_NOT_READY",
            message="Database connectivity or migration state is unavailable.",
        ) from exc
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    head = ScriptDirectory.from_config(config).get_current_head()
    if head is None or current != head:
        raise ApplicationError(
            status_code=503,
            code="MIGRATIONS_NOT_READY",
            message="Database migrations are not at the required revision.",
            details={"current_revision": current or "none"},
        )
    return ReadinessResponse(
        status="ready", database="ready", migrations="at_head", revision=head
    )
