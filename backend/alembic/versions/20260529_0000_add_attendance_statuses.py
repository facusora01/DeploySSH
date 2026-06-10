"""add attended and no_show statuses to appointmentstatus enum

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4f5e6
Create Date: 2026-05-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'a1b2c3d4f5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE appointmentstatus ADD VALUE IF NOT EXISTS 'ATTENDED'")
    op.execute("ALTER TYPE appointmentstatus ADD VALUE IF NOT EXISTS 'NO_SHOW'")


def downgrade() -> None:
    # PostgreSQL no soporta quitar valores de un enum existente.
    pass
