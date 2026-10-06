from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.core.errors import ApplicationError
from app.repositories.history import measurement_history

NOW = datetime(2026, 8, 15, tzinfo=UTC)


@pytest.mark.parametrize(
    ("duration", "raw"),
    [(timedelta(hours=24, seconds=1), True), (timedelta(days=31, seconds=1), False)],
)
def test_history_range_limits_reject_before_query(
    duration: timedelta, raw: bool
) -> None:
    session = MagicMock()
    with pytest.raises(ApplicationError) as caught:
        measurement_history(
            session,
            device_ids=[],
            period_start=NOW,
            period_end=NOW + duration,
            raw=raw,
        )
    assert caught.value.code == "HISTORY_RANGE_EXCEEDED"
    session.execute.assert_not_called()


def test_history_rejects_reversed_range() -> None:
    with pytest.raises(ApplicationError) as caught:
        measurement_history(
            MagicMock(),
            device_ids=[],
            period_start=NOW,
            period_end=NOW,
            raw=False,
        )
    assert caught.value.code == "INVALID_DATE_RANGE"
