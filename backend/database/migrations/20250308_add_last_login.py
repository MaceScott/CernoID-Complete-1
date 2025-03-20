"""Add last_login column to users table

Revision ID: 20250308_add_last_login
Revises: b7d8c2ae8ef5
Create Date: 2025-03-08 05:27:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250308_add_last_login'
down_revision: Union[str, None] = 'b7d8c2ae8ef5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users',
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('users', 'last_login') 