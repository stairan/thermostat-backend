"""create_new_daily_power_usage_table

Revision ID: 49bbffc8e5a9
Revises: 1be8233b83a5
Create Date: 2025-10-04 10:29:24.901585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49bbffc8e5a9'
down_revision: Union[str, Sequence[str], None] = '1be8233b83a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - rename old table and create new one."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Rename old table to preserve data
    if 'daily_power_usage' in inspector.get_table_names():
        op.execute("ALTER TABLE daily_power_usage RENAME TO daily_power_usage_old")

    # Create fresh new table with correct schema
    op.create_table(
        'daily_power_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('import_start_value', sa.Float(), nullable=False),
        sa.Column('import_end_value', sa.Float(), nullable=False),
        sa.Column('daily_import', sa.Float(), nullable=False),
        sa.Column('export_start_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('export_end_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('daily_export', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('inverter_daily_yield', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('daily_usage', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_power_usage_date'), 'daily_power_usage', ['date'], unique=True)
    op.create_index(op.f('ix_daily_power_usage_timestamp'), 'daily_power_usage', ['timestamp'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_daily_power_usage_timestamp'), table_name='daily_power_usage')
    op.drop_index(op.f('ix_daily_power_usage_date'), table_name='daily_power_usage')
    op.drop_table('daily_power_usage')

    # Restore old table
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'daily_power_usage_old' in inspector.get_table_names():
        op.execute("ALTER TABLE daily_power_usage_old RENAME TO daily_power_usage")
