"""add profesional public link

Revision ID: 999999999999
Revises: 202b86e061d9
Create Date: 2026-05-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '999999999999'
down_revision: Union[str, None] = '202b86e061d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'profesionales',
        sa.Column('public_link', sa.String(length=100), nullable=True),
    )
    op.create_index(
        op.f('ix_profesionales_public_link'),
        'profesionales',
        ['public_link'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_profesionales_public_link'), table_name='profesionales')
    op.drop_column('profesionales', 'public_link')
