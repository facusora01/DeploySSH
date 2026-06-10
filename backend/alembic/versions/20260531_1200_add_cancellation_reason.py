"""add cancellation_reason to appointments

Revision ID: d5e6f7g8h9i0
Revises: e5f6a7b8c9d0
Create Date: 2026-05-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7g8h9i0'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('appointments', sa.Column('cancellation_reason', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('appointments', 'cancellation_reason')
