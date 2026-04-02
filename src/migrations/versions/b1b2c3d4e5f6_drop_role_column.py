"""drop role column from users

Revision ID: b1b2c3d4e5f6
Revises: a1b2c3d4e5f6
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa

revision = 'b1b2c3d4e5f6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.drop_column('users', 'role')

def downgrade() -> None:
    op.add_column('users', sa.Column('role', sa.Enum('ADMIN', 'STAFF', 'USER', 'ANY', 'OPTIONAL', name='roletype'), nullable=False))