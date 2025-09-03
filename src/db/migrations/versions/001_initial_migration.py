"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-09-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create accounts table
    op.create_table('accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.Enum('bank', 'wallet', 'cash', 'other', name='accounttype', native_enum=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create account_balances table
    op.create_table('account_balances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('balance', sa.Numeric(precision=20, scale=8), nullable=False, default=0),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('balance >= 0', name='ck_balance_non_negative'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'currency', name='uq_account_currency')
    )
    op.create_index('ix_account_balances_account_id', 'account_balances', ['account_id'])
    
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('income', 'expense', 'transfer', 'conversion', name='transactiontype', native_enum=True), nullable=False),
        sa.Column('account_from_id', sa.Integer(), nullable=True),
        sa.Column('account_to_id', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('currency_to', sa.String(length=10), nullable=True),
        sa.Column('amount_to', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('exchange_rate', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('amount > 0', name='ck_amount_positive'),
        sa.CheckConstraint('amount_to IS NULL OR amount_to > 0', name='ck_amount_to_positive'),
        sa.CheckConstraint('exchange_rate IS NULL OR exchange_rate > 0', name='ck_rate_positive'),
        sa.ForeignKeyConstraint(['account_from_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['account_to_id'], ['accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transactions_date', 'transactions', ['date'])
    op.create_index('ix_transactions_type', 'transactions', ['type'])
    
    # Create exchange_rates table
    op.create_table('exchange_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pair', sa.String(length=20), nullable=False),
        sa.Column('value', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('value > 0', name='ck_rate_value_positive'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_exchange_rates_pair', 'exchange_rates', ['pair'])
    op.create_index('ix_exchange_rates_fetched_at', 'exchange_rates', ['fetched_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('exchange_rates')
    op.drop_table('transactions')
    op.drop_table('account_balances')
    op.drop_table('accounts')
    
    # Drop custom enums
    sa.Enum(name='accounttype').drop(op.get_bind())
    sa.Enum(name='transactiontype').drop(op.get_bind())