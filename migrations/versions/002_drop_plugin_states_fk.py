"""Drop foreign key constraint on plugin_states.

Revision ID: 002_drop_plugin_states_fk
Revises: 001_initial
Create Date: 2026-01-06

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_drop_plugin_states_fk"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the foreign key constraint - plugin_states doesn't need it
    # since bots are loaded from YAML config, not the database
    op.drop_constraint("plugin_states_bot_id_fkey", "plugin_states", type_="foreignkey")


def downgrade() -> None:
    op.create_foreign_key(
        "plugin_states_bot_id_fkey",
        "plugin_states",
        "bots",
        ["bot_id"],
        ["id"],
        ondelete="CASCADE",
    )
