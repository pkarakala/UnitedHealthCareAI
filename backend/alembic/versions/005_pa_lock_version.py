"""add lock_version to prior_auths for optimistic concurrency

Revision ID: 005
Revises: 004
Create Date: 2026-07-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'prior_auths',
        sa.Column('lock_version', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('prior_auths', 'lock_version')
