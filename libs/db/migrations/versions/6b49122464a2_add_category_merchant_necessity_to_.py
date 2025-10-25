"""add_category_merchant_necessity_to_transactions

Revision ID: 6b49122464a2
Revises: a0b6f1825403
Create Date: 2025-10-25 16:56:36.394582

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6b49122464a2"
down_revision = "a0b6f1825403"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add category_id, merchant_id, and is_necessary to transactions table
    op.add_column(
        "transactions",
        sa.Column("category_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("merchant_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("is_necessary", sa.Boolean(), nullable=True),
    )

    # Add foreign key constraints
    op.create_foreign_key(
        "fk_transactions_category_id",
        "transactions",
        "categories",
        ["category_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_transactions_merchant_id",
        "transactions",
        "merchants",
        ["merchant_id"],
        ["id"],
    )

    # Add indexes for better query performance
    op.create_index(
        "ix_transactions_category_id",
        "transactions",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_merchant_id",
        "transactions",
        ["merchant_id"],
        unique=False,
    )

    # Add the same columns to pending_transactions table
    op.add_column(
        "pending_transactions",
        sa.Column("category_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "pending_transactions",
        sa.Column("merchant_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "pending_transactions",
        sa.Column("is_necessary", sa.Boolean(), nullable=True),
    )

    # Add foreign key constraints for pending_transactions
    op.create_foreign_key(
        "fk_pending_transactions_category_id",
        "pending_transactions",
        "categories",
        ["category_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_pending_transactions_merchant_id",
        "pending_transactions",
        "merchants",
        ["merchant_id"],
        ["id"],
    )

    # Add indexes for pending_transactions
    op.create_index(
        "ix_pending_transactions_category_id",
        "pending_transactions",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        "ix_pending_transactions_merchant_id",
        "pending_transactions",
        ["merchant_id"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes for pending_transactions
    op.drop_index("ix_pending_transactions_merchant_id", table_name="pending_transactions")
    op.drop_index("ix_pending_transactions_category_id", table_name="pending_transactions")

    # Drop foreign key constraints for pending_transactions
    op.drop_constraint("fk_pending_transactions_merchant_id", "pending_transactions", type_="foreignkey")
    op.drop_constraint("fk_pending_transactions_category_id", "pending_transactions", type_="foreignkey")

    # Drop columns from pending_transactions
    op.drop_column("pending_transactions", "is_necessary")
    op.drop_column("pending_transactions", "merchant_id")
    op.drop_column("pending_transactions", "category_id")

    # Drop indexes for transactions
    op.drop_index("ix_transactions_merchant_id", table_name="transactions")
    op.drop_index("ix_transactions_category_id", table_name="transactions")

    # Drop foreign key constraints for transactions
    op.drop_constraint("fk_transactions_merchant_id", "transactions", type_="foreignkey")
    op.drop_constraint("fk_transactions_category_id", "transactions", type_="foreignkey")

    # Drop columns from transactions
    op.drop_column("transactions", "is_necessary")
    op.drop_column("transactions", "merchant_id")
    op.drop_column("transactions", "category_id")
