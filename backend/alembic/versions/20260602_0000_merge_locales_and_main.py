"""merge locales branch into main migration chain

Revision ID: f6g7h8i9j0k1
Revises: d5e6f7g8h9i0, d1e2f3a4b5c6
Create Date: 2026-06-02 00:00:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, Sequence[str], None] = ('d5e6f7g8h9i0', 'd1e2f3a4b5c6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
