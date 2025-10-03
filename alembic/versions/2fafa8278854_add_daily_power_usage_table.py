"""add_daily_power_usage_table

Revision ID: 2fafa8278854
Revises: 
Create Date: 2025-10-03 19:21:50.506242

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fafa8278854'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'daily_power_usage' not in inspector.get_table_names():
        # Create table from scratch
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
    else:
        # Table exists, check for missing columns and add them
        columns = [col['name'] for col in inspector.get_columns('daily_power_usage')]

        if 'import_start_value' not in columns:
            op.add_column('daily_power_usage', sa.Column('import_start_value', sa.Float(), nullable=True))
        if 'import_end_value' not in columns:
            op.add_column('daily_power_usage', sa.Column('import_end_value', sa.Float(), nullable=True))
        if 'daily_import' not in columns:
            op.add_column('daily_power_usage', sa.Column('daily_import', sa.Float(), nullable=True))
        if 'export_start_value' not in columns:
            op.add_column('daily_power_usage', sa.Column('export_start_value', sa.Float(), nullable=True, server_default='0.0'))
        if 'export_end_value' not in columns:
            op.add_column('daily_power_usage', sa.Column('export_end_value', sa.Float(), nullable=True, server_default='0.0'))
        if 'daily_export' not in columns:
            op.add_column('daily_power_usage', sa.Column('daily_export', sa.Float(), nullable=True, server_default='0.0'))
        if 'inverter_daily_yield' not in columns:
            op.add_column('daily_power_usage', sa.Column('inverter_daily_yield', sa.Float(), nullable=True, server_default='0.0'))
        if 'daily_usage' not in columns:
            op.add_column('daily_power_usage', sa.Column('daily_usage', sa.Float(), nullable=True))
        if 'timestamp' not in columns:
            op.add_column('daily_power_usage', sa.Column('timestamp', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the entire table
    op.drop_index(op.f('ix_daily_power_usage_timestamp'), table_name='daily_power_usage')
    op.drop_index(op.f('ix_daily_power_usage_date'), table_name='daily_power_usage')
    op.drop_table('daily_power_usage')
