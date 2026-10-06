"""seed the fixed operational settings contract"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SETTING_ROWS = [
    {
        "key": "demand_limit_kw",
        "value_json": 50.0,
        "description": "Site demand warning limit in kilowatts.",
    },
    {
        "key": "demand_interval_minutes",
        "value_json": 15,
        "description": "Demand aggregation interval in minutes.",
    },
    {
        "key": "tariff_zar_per_kwh",
        "value_json": 3.0,
        "description": "Energy tariff in South African rand per kilowatt-hour.",
    },
    {
        "key": "timezone",
        "value_json": "Africa/Johannesburg",
        "description": "IANA timezone used for dashboard periods.",
    },
    {
        "key": "online_timeout_seconds",
        "value_json": 10,
        "description": "Maximum measurement age considered online.",
    },
    {
        "key": "stale_timeout_seconds",
        "value_json": 60,
        "description": "Maximum measurement age considered stale before offline.",
    },
    {
        "key": "simulator_profile",
        "value_json": "normal",
        "description": "Selected simulator operating profile.",
    },
]


def upgrade() -> None:
    settings = sa.table(
        "settings",
        sa.column("key", sa.String()),
        sa.column("value_json", sa.JSON()),
        sa.column("description", sa.Text()),
    )
    op.bulk_insert(settings, SETTING_ROWS)


def downgrade() -> None:
    keys = [row["key"] for row in SETTING_ROWS]
    settings = sa.table("settings", sa.column("key", sa.String()))
    op.execute(settings.delete().where(settings.c.key.in_(keys)))
