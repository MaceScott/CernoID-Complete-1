"""Initial database migration.

Revision ID: 20240220_000000
Revises: 
Create Date: 2024-02-20 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = '20240220_000000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Create initial tables."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email')),
        sa.UniqueConstraint('username', name=op.f('uq_users_username'))
    )
    
    # Create face_encodings table
    op.create_table(
        'face_encodings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('encoding', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name=op.f('fk_face_encodings_user_id_users'),
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_face_encodings'))
    )
    
    # Create access_logs table
    op.create_table(
        'access_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('access_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name=op.f('fk_access_logs_user_id_users'),
            ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_access_logs'))
    )
    
    # Create indexes
    op.create_index(
        op.f('ix_users_email'),
        'users', ['email'],
        unique=True
    )
    op.create_index(
        op.f('ix_users_username'),
        'users', ['username'],
        unique=True
    )
    op.create_index(
        op.f('ix_face_encodings_user_id'),
        'face_encodings', ['user_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_access_logs_created_at'),
        'access_logs', ['created_at'],
        unique=False
    )
    op.create_index(
        op.f('ix_access_logs_user_id'),
        'access_logs', ['user_id'],
        unique=False
    )

def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('access_logs')
    op.drop_table('face_encodings')
    op.drop_table('users') 