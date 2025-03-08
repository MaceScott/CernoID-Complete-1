"""Initial migration

Revision ID: d85c9ea0ca4f
Revises: 1034977a6380
Create Date: 2025-03-08 00:06:16.587604

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd85c9ea0ca4f'
down_revision: Union[str, None] = '1034977a6380'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Table already exists, no need to create it
    pass


def downgrade() -> None:
    # Don't drop the table on downgrade
    pass 