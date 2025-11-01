"""Convert enum columns to strings

Revision ID: 0002
Revises: 0001
Create Date: 2024-11-01 15:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert ENUM columns to VARCHAR for better compatibility
    
    # Goals table
    op.alter_column('goals', 'goal_type',
                    existing_type=mysql.ENUM('count', 'sum', 'streak', 'milestone', 'open', name='goaltype'),
                    type_=sa.String(20),
                    existing_nullable=False)
    
    op.alter_column('goals', 'timeframe_type',
                    existing_type=mysql.ENUM('fixed', 'rolling', 'recurring', name='timeframetype'),
                    type_=sa.String(20),
                    existing_nullable=False)
    
    op.alter_column('goals', 'privacy',
                    existing_type=mysql.ENUM('public', 'unlisted', 'private', name='privacylevel'),
                    type_=sa.String(20),
                    existing_nullable=False)
    
    op.alter_column('goals', 'status',
                    existing_type=mysql.ENUM('draft', 'active', 'ended', name='goalstatus'),
                    type_=sa.String(20),
                    existing_nullable=False)
    
    # Goal members table
    op.alter_column('goal_members', 'role',
                    existing_type=mysql.ENUM('owner', 'editor', 'member', 'viewer', name='memberrole'),
                    type_=sa.String(20),
                    existing_nullable=False)


def downgrade() -> None:
    # Convert back to ENUM (if needed)
    op.alter_column('goal_members', 'role',
                    existing_type=sa.String(20),
                    type_=mysql.ENUM('owner', 'editor', 'member', 'viewer', name='memberrole'),
                    existing_nullable=False)
    
    op.alter_column('goals', 'status',
                    existing_type=sa.String(20),
                    type_=mysql.ENUM('draft', 'active', 'ended', name='goalstatus'),
                    existing_nullable=False)
    
    op.alter_column('goals', 'privacy',
                    existing_type=sa.String(20),
                    type_=mysql.ENUM('public', 'unlisted', 'private', name='privacylevel'),
                    existing_nullable=False)
    
    op.alter_column('goals', 'timeframe_type',
                    existing_type=sa.String(20),
                    type_=mysql.ENUM('fixed', 'rolling', 'recurring', name='timeframetype'),
                    existing_nullable=False)
    
    op.alter_column('goals', 'goal_type',
                    existing_type=sa.String(20),
                    type_=mysql.ENUM('count', 'sum', 'streak', 'milestone', 'open', name='goaltype'),
                    existing_nullable=False)

