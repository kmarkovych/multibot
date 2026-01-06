"""Add bot_statistics table for hourly aggregated stats.

Revision ID: 003_add_bot_statistics
Revises: 002_drop_plugin_states_fk
Create Date: 2026-01-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_add_bot_statistics"
down_revision: str | None = "002_drop_plugin_states_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create bot_statistics table for hourly aggregated statistics
    op.create_table(
        "bot_statistics",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("bot_id", sa.String(64), nullable=False),
        sa.Column("hour_bucket", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("command_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("callback_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("command_usage", postgresql.JSONB(), nullable=True),
    )

    # Create unique index on (bot_id, hour_bucket) for upsert operations
    op.create_index(
        "ix_bot_statistics_bot_hour",
        "bot_statistics",
        ["bot_id", "hour_bucket"],
        unique=True,
    )

    # Create index on hour_bucket for time-based queries
    op.create_index(
        "ix_bot_statistics_hour",
        "bot_statistics",
        ["hour_bucket"],
    )


def downgrade() -> None:
    op.drop_index("ix_bot_statistics_hour", table_name="bot_statistics")
    op.drop_index("ix_bot_statistics_bot_hour", table_name="bot_statistics")
    op.drop_table("bot_statistics")
