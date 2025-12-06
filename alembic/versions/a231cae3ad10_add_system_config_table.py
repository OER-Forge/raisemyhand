"""Add system_config table

Revision ID: a231cae3ad10
Revises: c6671aaf91d2
Create Date: 2025-12-06 09:13:00.343565

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a231cae3ad10'
down_revision: Union[str, None] = 'c6671aaf91d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'system_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_type', sa.String(length=20), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_config_id'), 'system_config', ['id'], unique=False)
    op.create_index(op.f('ix_system_config_key'), 'system_config', ['key'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_system_config_key'), table_name='system_config')
    op.drop_index(op.f('ix_system_config_id'), table_name='system_config')
    op.drop_table('system_config')
