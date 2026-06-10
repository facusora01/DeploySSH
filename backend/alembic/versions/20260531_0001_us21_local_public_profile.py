"""US-21: local public profile fields and profesional-local association

Revision ID: d1e2f3a4b5c6
Revises: c4d5e6f7g8h9
Create Date: 2026-05-31 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c4d5e6f7g8h9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('locales', sa.Column('public_link', sa.String(length=100), nullable=True))
    op.add_column('locales', sa.Column('logo_url', sa.Text(), nullable=True))
    op.add_column('locales', sa.Column('opening_hours', sa.JSON(), nullable=True))
    op.create_unique_constraint('uq_locales_public_link', 'locales', ['public_link'])

    op.add_column('profesionales', sa.Column('local_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_profesionales_local_id',
        'profesionales', 'locales',
        ['local_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_profesionales_local_id', 'profesionales', type_='foreignkey')
    op.drop_column('profesionales', 'local_id')

    op.drop_constraint('uq_locales_public_link', 'locales', type_='unique')
    op.drop_column('locales', 'opening_hours')
    op.drop_column('locales', 'logo_url')
    op.drop_column('locales', 'public_link')
