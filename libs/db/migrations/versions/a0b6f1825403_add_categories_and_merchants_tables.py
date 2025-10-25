"""add_categories_and_merchants_tables

Revision ID: a0b6f1825403
Revises: c2a98e5201cb
Create Date: 2025-10-25 16:40:28.609551

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a0b6f1825403"
down_revision = "c2a98e5201cb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create categories table without enum - use varchar instead
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_user_category_name"),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"], unique=False)

    # Add check constraint for type values
    op.create_check_constraint(
        "ck_category_type",
        "categories",
        "type IN ('income', 'expense')"
    )

    # Create merchants table
    op.create_table(
        "merchants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_user_merchant_name"),
    )
    op.create_index("ix_merchants_user_id", "merchants", ["user_id"], unique=False)


def downgrade() -> None:
    # Drop merchants table
    op.drop_index("ix_merchants_user_id", table_name="merchants")
    op.drop_table("merchants")

    # Drop categories table
    op.drop_constraint("ck_category_type", "categories", type_="check")
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_table("categories")
