"""Create users table

Revision ID: 003
Revises: 2e5aa12f0766
Create Date: 2025-09-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '2e5aa12f0766'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_user_id', sa.String(length=50), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('language_code', sa.String(length=10), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_user_id')
    )
    op.create_index('ix_users_telegram_user_id', 'users', ['telegram_user_id'])

    # Fix pending_transactions user_id column type and add FK constraint
    # First clear any existing data to avoid casting issues
    op.execute("DELETE FROM pending_transactions")

    # Alter user_id column from String to Integer using raw SQL
    op.execute("ALTER TABLE pending_transactions ALTER COLUMN user_id TYPE INTEGER USING user_id::integer")
    op.execute("ALTER TABLE pending_transactions ALTER COLUMN user_id SET NOT NULL")

    # Add foreign key constraint
    op.create_foreign_key('fk_pending_transactions_user_id',
                         'pending_transactions', 'users',
                         ['user_id'], ['id'])


def downgrade() -> None:
    op.drop_table('users')
