"""add deposit fields to services and appointments

Revision ID: a1b2c3d4f5e6
Revises: b7c2f3e4d5a6
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4f5e6'
down_revision: Union[str, None] = 'b7c2f3e4d5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE depositstatus AS ENUM ('NONE', 'PENDING', 'PAID')")

    op.add_column('services',
        sa.Column('deposit_active', sa.Boolean(), server_default='false', nullable=False)
    )
    op.add_column('services',
        sa.Column('deposit_amount', sa.Numeric(precision=10, scale=2), nullable=True)
    )
    op.add_column('services',
        sa.Column('deposit_required', sa.Boolean(), server_default='false', nullable=False)
    )

    op.add_column('appointments',
        sa.Column('deposit_status', sa.Enum('NONE', 'PENDING', 'PAID', name='depositstatus'),
                  server_default='NONE', nullable=False)
    )


def downgrade() -> None:
    op.drop_column('appointments', 'deposit_status')
    op.execute("DROP TYPE depositstatus")

    op.drop_column('services', 'deposit_required')
    op.drop_column('services', 'deposit_amount')
    op.drop_column('services', 'deposit_active')
