"""add source blocking fields

Revision ID: f6a9b3c1d2e4
Revises: e4f7c9a2b1d0
Create Date: 2026-02-25 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6a9b3c1d2e4"
down_revision: Union[str, None] = "e4f7c9a2b1d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("sources", sa.Column("blocked_reason", sa.Text(), nullable=True))
    op.add_column("sources", sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sources", sa.Column("last_error", sa.Text(), nullable=True))
    op.alter_column("sources", "is_blocked", server_default=None)


def downgrade() -> None:
    op.drop_column("sources", "last_error")
    op.drop_column("sources", "blocked_at")
    op.drop_column("sources", "blocked_reason")
    op.drop_column("sources", "is_blocked")
