"""remove negative balance constraint for logging mode

Revision ID: 003_remove_constraint
Revises: 002_balance_tracking
Create Date: 2025-09-19 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003_remove_constraint"
down_revision = "002_balance_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove the check constraint that prevents negative balances
    op.drop_constraint('ck_balance_non_negative', 'account_balances', type_='check')


def downgrade() -> None:
    # Re-add the check constraint
    op.create_check_constraint('ck_balance_non_negative', 'account_balances', 'balance >= 0')
