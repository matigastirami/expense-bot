"""add_pending_transactions_table

Revision ID: 2e5aa12f0766
Revises: 001
Create Date: 2025-09-03 04:06:19.898141

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2e5aa12f0766"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'pending_transactions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('transaction_type', sa.Enum('income', 'expense', 'transfer', 'conversion', name='transactiontype', native_enum=False), nullable=False),
        sa.Column('account_from_id', sa.Integer, sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('account_to_id', sa.Integer, sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('currency', sa.String(10), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('currency_to', sa.String(10), nullable=True),
        sa.Column('amount_to', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('exchange_rate', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(50), nullable=True),  # For Telegram user tracking
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('amount > 0', name='ck_pending_amount_positive'),
        sa.CheckConstraint('amount_to IS NULL OR amount_to > 0', name='ck_pending_amount_to_positive'),
        sa.CheckConstraint('retry_count >= 0', name='ck_pending_retry_count_non_negative'),
    )
    
    op.create_index('ix_pending_transactions_created_at', 'pending_transactions', ['created_at'])
    op.create_index('ix_pending_transactions_retry_count', 'pending_transactions', ['retry_count'])


def downgrade() -> None:
    op.drop_index('ix_pending_transactions_retry_count', table_name='pending_transactions')
    op.drop_index('ix_pending_transactions_created_at', table_name='pending_transactions')
    op.drop_table('pending_transactions')
