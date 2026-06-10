"""Add local_invitations table (invite professionals to team)

Revision ID: a7b8c9d0e1f2
Revises: b65fa1f4138b
Create Date: 2026-06-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'b65fa1f4138b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'local_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('local_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['local_id'], ['locales.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_local_invitations_token_hash'),
    )
    op.create_index('ix_local_invitations_local_id', 'local_invitations', ['local_id'])
    op.create_index('ix_local_invitations_email', 'local_invitations', ['email'])


def downgrade() -> None:
    op.drop_index('ix_local_invitations_email', table_name='local_invitations')
    op.drop_index('ix_local_invitations_local_id', table_name='local_invitations')
    op.drop_table('local_invitations')
