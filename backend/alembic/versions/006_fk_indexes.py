"""add indexes on prior_auth_id FKs for timeline/detail queries

Revision ID: 006
Revises: 005
Create Date: 2026-07-23
"""
from typing import Sequence, Union
from alembic import op

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = [
    ("ix_communications_prior_auth_id", "communications"),
    ("ix_clinical_documents_prior_auth_id", "clinical_documents"),
    ("ix_appeals_prior_auth_id", "appeals"),
    ("ix_agent_executions_prior_auth_id", "agent_executions"),
]


def upgrade() -> None:
    for name, table in INDEXES:
        op.create_index(name, table, ["prior_auth_id"])


def downgrade() -> None:
    for name, table in INDEXES:
        op.drop_index(name, table_name=table)
