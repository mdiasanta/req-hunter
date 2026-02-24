"""add url_path_filter to sources

Revision ID: a1b2c3d4e5f6
Revises: d8cb6f6038e7
Create Date: 2026-02-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd8cb6f6038e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sources', sa.Column('url_path_filter', sa.String(length=256), nullable=True))


def downgrade() -> None:
    op.drop_column('sources', 'url_path_filter')
