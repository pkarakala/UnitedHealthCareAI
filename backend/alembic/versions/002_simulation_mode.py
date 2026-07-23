"""add is_simulated columns to prior_auths

Revision ID: 002
Revises: 001
Create Date: 2026-07-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('prior_auths', sa.Column('is_simulated', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('prior_auths', sa.Column('simulated_agents', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('prior_auths', 'simulated_agents')
    op.drop_column('prior_auths', 'is_simulated')
