"""add form fields tables

Revision ID: a3f1e2d4c5b6
Revises: 895e0c19e7bc
Create Date: 2026-05-26 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f1e2d4c5b6'
down_revision: Union[str, None] = '895e0c19e7bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'form_fields',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('profesional_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(length=200), nullable=False),
        sa.Column('is_required', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['profesional_id'], ['profesionales.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'form_field_responses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('appointment_id', sa.Uuid(), nullable=False),
        sa.Column('field_id', sa.Uuid(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.ForeignKeyConstraint(['field_id'], ['form_fields.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('form_field_responses')
    op.drop_table('form_fields')
