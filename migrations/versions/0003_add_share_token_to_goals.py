"""Add share_token to goals

Revision ID: 0003
Revises: 0002
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add share_token column to goals table
    op.add_column('goals', sa.Column('share_token', sa.String(length=36), nullable=True))
    
    # Create unique index on share_token
    op.create_index(op.f('ix_goals_share_token'), 'goals', ['share_token'], unique=True)


def downgrade() -> None:
    # Drop index and column
    op.drop_index(op.f('ix_goals_share_token'), table_name='goals')
    op.drop_column('goals', 'share_token')

