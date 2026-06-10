"""add client notes

Revision ID: f6a7b8c9d0e1
Revises: d5e6f7g8h9i0
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'd5e6f7g8h9i0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'client_notes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('profesional_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['profesional_id'], ['profesionales.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_client_notes_profesional_client',
        'client_notes',
        ['profesional_id', 'client_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_client_notes_profesional_client', table_name='client_notes')
    op.drop_table('client_notes')
