"""merge client_notes and locales heads

Revision ID: b65fa1f4138b
Revises: f6a7b8c9d0e1, f6g7h8i9j0k1
Create Date: 2026-06-02 15:51:18.737025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b65fa1f4138b'
down_revision: Union[str, None] = ('f6a7b8c9d0e1', 'f6g7h8i9j0k1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass