"""Add token billing system tables.

Revision ID: 004_token_system
Revises: 003_add_bot_statistics
Create Date: 2026-01-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_token_system"
down_revision: str | None = "003_add_bot_statistics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create user_tokens table for token balances
    op.create_table(
        "user_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("bot_id", sa.String(64), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_purchased", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_consumed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create unique index on (telegram_id, bot_id) for lookups
    op.create_index(
        "ix_user_tokens_telegram_bot",
        "user_tokens",
        ["telegram_id", "bot_id"],
        unique=True,
    )

    # Create index on bot_id for bot-level queries
    op.create_index(
        "ix_user_tokens_bot_id",
        "user_tokens",
        ["bot_id"],
    )

    # Create token_transactions table for transaction history
    op.create_table(
        "token_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("bot_id", sa.String(64), nullable=False),
        sa.Column(
            "transaction_type", sa.String(32), nullable=False
        ),  # purchase, consume, grant, refund
        sa.Column(
            "amount", sa.Integer(), nullable=False
        ),  # Positive=credit, negative=debit
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column(
            "reference_type", sa.String(64), nullable=True
        ),  # payment, action, welcome
        sa.Column(
            "reference_id", sa.String(128), nullable=True
        ),  # Payment ID, action name
        sa.Column("stars_paid", sa.Integer(), nullable=True),  # For purchases
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create index for user transaction lookups
    op.create_index(
        "ix_token_transactions_user_bot",
        "token_transactions",
        ["telegram_id", "bot_id"],
    )

    # Create index for time-based queries
    op.create_index(
        "ix_token_transactions_created",
        "token_transactions",
        ["created_at"],
    )

    # Create index for transaction type queries
    op.create_index(
        "ix_token_transactions_type",
        "token_transactions",
        ["transaction_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_token_transactions_type", table_name="token_transactions")
    op.drop_index("ix_token_transactions_created", table_name="token_transactions")
    op.drop_index("ix_token_transactions_user_bot", table_name="token_transactions")
    op.drop_table("token_transactions")

    op.drop_index("ix_user_tokens_bot_id", table_name="user_tokens")
    op.drop_index("ix_user_tokens_telegram_bot", table_name="user_tokens")
    op.drop_table("user_tokens")
