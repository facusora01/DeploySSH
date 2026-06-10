"""add field_type and options to form_fields

Revision ID: b7c2f3e4d5a6
Revises: a3f1e2d4c5b6
Create Date: 2026-05-26 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c2f3e4d5a6'
down_revision: Union[str, None] = 'a3f1e2d4c5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'form_fields',
        sa.Column('field_type', sa.String(20), server_default='text', nullable=False),
    )
    op.add_column(
        'form_fields',
        sa.Column('options', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('form_fields', 'options')
    op.drop_column('form_fields', 'field_type')
