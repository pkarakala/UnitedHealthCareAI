"""widen PHI columns for encryption at rest

Fernet ciphertext is base64 and longer than the plaintext it replaces, so the
phone/email columns are widened to TEXT. clinical_summary and
medical_necessity_letter are already TEXT. This migration is schema-only; it does
not backfill existing rows — decrypt_phi returns legacy plaintext unchanged.

Revision ID: 004
Revises: 003
Create Date: 2026-07-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('patients', 'phone', type_=sa.Text(), existing_nullable=True)
    op.alter_column('patients', 'email', type_=sa.Text(), existing_nullable=True)


def downgrade() -> None:
    op.alter_column('patients', 'phone', type_=sa.String(20), existing_nullable=True)
    op.alter_column('patients', 'email', type_=sa.String(255), existing_nullable=True)
