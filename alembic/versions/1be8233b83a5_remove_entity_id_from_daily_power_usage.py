"""remove_entity_id_from_daily_power_usage

Revision ID: 1be8233b83a5
Revises: 2fafa8278854
Create Date: 2025-10-04 09:55:03.025633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1be8233b83a5'
down_revision: Union[str, Sequence[str], None] = '2fafa8278854'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - remove entity_id column if it exists."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Check if table and column exist
    if 'daily_power_usage' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('daily_power_usage')]

        if 'entity_id' in columns:
            # SQLite doesn't support DROP COLUMN directly, need to recreate table
            # Drop temp table if it exists from previous failed migration
            op.execute("DROP TABLE IF EXISTS daily_power_usage_new")

            op.execute("""
                CREATE TABLE daily_power_usage_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    import_start_value REAL NOT NULL,
                    import_end_value REAL NOT NULL,
                    daily_import REAL NOT NULL,
                    export_start_value REAL NOT NULL DEFAULT 0.0,
                    export_end_value REAL NOT NULL DEFAULT 0.0,
                    daily_export REAL NOT NULL DEFAULT 0.0,
                    inverter_daily_yield REAL NOT NULL DEFAULT 0.0,
                    daily_usage REAL NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            """)

            # Copy data from old table to new (excluding entity_id)
            op.execute("""
                INSERT INTO daily_power_usage_new
                (id, date, import_start_value, import_end_value, daily_import,
                 export_start_value, export_end_value, daily_export,
                 inverter_daily_yield, daily_usage, timestamp)
                SELECT id, date, import_start_value, import_end_value, daily_import,
                       export_start_value, export_end_value, daily_export,
                       inverter_daily_yield, daily_usage, timestamp
                FROM daily_power_usage
            """)

            # Drop old table
            op.execute("DROP TABLE daily_power_usage")

            # Rename new table
            op.execute("ALTER TABLE daily_power_usage_new RENAME TO daily_power_usage")

            # Recreate indexes
            op.create_index(op.f('ix_daily_power_usage_date'), 'daily_power_usage', ['date'], unique=True)
            op.create_index(op.f('ix_daily_power_usage_timestamp'), 'daily_power_usage', ['timestamp'], unique=False)


def downgrade() -> None:
    """Downgrade schema - add entity_id column back."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'daily_power_usage' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('daily_power_usage')]

        if 'entity_id' not in columns:
            op.add_column('daily_power_usage',
                         sa.Column('entity_id', sa.String(), nullable=True))
