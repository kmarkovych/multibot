"""Initial migration - create core tables.

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create bots table
    op.create_table(
        "bots",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("mode", sa.String(16), server_default="polling"),
        sa.Column("webhook_url", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_json", postgresql.JSONB(), nullable=True),
    )

    # Create bot_users table
    op.create_table(
        "bot_users",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column(
            "bot_id",
            sa.String(64),
            sa.ForeignKey("bots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("language_code", sa.String(10), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
    )
    op.create_index(
        "ix_bot_users_telegram_bot",
        "bot_users",
        ["telegram_id", "bot_id"],
        unique=True,
    )
    op.create_index("ix_bot_users_bot_id", "bot_users", ["bot_id"])

    # Create bot_events table
    op.create_table(
        "bot_events",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column(
            "bot_id",
            sa.String(64),
            sa.ForeignKey("bots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_bot_events_bot_created", "bot_events", ["bot_id", "created_at"])
    op.create_index("ix_bot_events_type", "bot_events", ["event_type"])

    # Create plugin_states table
    op.create_table(
        "plugin_states",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column(
            "bot_id",
            sa.String(64),
            sa.ForeignKey("bots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plugin_name", sa.String(128), nullable=False),
        sa.Column("state_key", sa.String(255), nullable=False),
        sa.Column("state_value", postgresql.JSONB(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_plugin_states_unique",
        "plugin_states",
        ["bot_id", "plugin_name", "state_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("plugin_states")
    op.drop_table("bot_events")
    op.drop_table("bot_users")
    op.drop_table("bots")
