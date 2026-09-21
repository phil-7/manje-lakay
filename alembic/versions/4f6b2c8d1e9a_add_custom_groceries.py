"""add calendar-scoped custom groceries

Revision ID: 4f6b2c8d1e9a
Revises: 9a3e6f1b2c4d
Create Date: 2026-09-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f6b2c8d1e9a"
down_revision: Union[str, Sequence[str], None] = "9a3e6f1b2c4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "custom_groceries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_custom_groceries_id", "custom_groceries", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_custom_groceries_id", table_name="custom_groceries")
    op.drop_table("custom_groceries")