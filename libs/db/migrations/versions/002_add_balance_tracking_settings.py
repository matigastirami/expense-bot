"""add balance tracking settings

Revision ID: 002_balance_tracking
Revises: 1205b25116b9
Create Date: 2025-09-18 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_balance_tracking"
down_revision = "1205b25116b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for balance tracking mode
    balance_tracking_mode_enum = sa.Enum('strict', 'logging', name='balancetrackingmode', native_enum=True)
    balance_tracking_mode_enum.create(op.get_bind())

    # Add balance_tracking_mode column to users table
    op.add_column('users', sa.Column('balance_tracking_mode',
                                   sa.Enum('strict', 'logging', name='balancetrackingmode', native_enum=True),
                                   nullable=False,
                                   server_default='strict'))

    # Add track_balance column to accounts table
    op.add_column('accounts', sa.Column('track_balance', sa.Boolean(), nullable=True))

    # Set default values for existing users and accounts
    op.execute("UPDATE users SET balance_tracking_mode = 'strict' WHERE balance_tracking_mode IS NULL")
    # Leave track_balance as NULL for accounts - this will inherit from user setting


def downgrade() -> None:
    # Drop columns
    op.drop_column('accounts', 'track_balance')
    op.drop_column('users', 'balance_tracking_mode')

    # Drop enum type
    balance_tracking_mode_enum = sa.Enum('strict', 'logging', name='balancetrackingmode', native_enum=True)
    balance_tracking_mode_enum.drop(op.get_bind())
