"""add refresh_tokens table

Revision ID: a1b2c3d4e5f6
Revises: 7fa41ff5d127_
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '7fa41ff5d127_'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Uuid(), nullable=False, primary_key=True),
        sa.Column('token_hash', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.Uuid(), nullable=False, foreign_key('users.id'), index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('refresh_tokens')
