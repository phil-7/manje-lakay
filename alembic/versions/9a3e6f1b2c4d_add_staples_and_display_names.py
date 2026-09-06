"""add staples and title-case ingredient names

Revision ID: 9a3e6f1b2c4d
Revises: 677e8b7b509c
Create Date: 2026-09-06
"""
from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision: str = "9a3e6f1b2c4d"
down_revision: Union[str, Sequence[str], None] = "677e8b7b509c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _title_case(value: str) -> str:
    return " ".join(value.strip().split()).title()


def upgrade() -> None:
    with op.batch_alter_table("recipes") as batch_op:
        batch_op.add_column(
            sa.Column("is_staple", sa.Boolean(), nullable=False, server_default=sa.false())
        )

    connection = op.get_bind()
    ingredients = connection.execute(sa.text("SELECT id, name FROM ingredients")).fetchall()
    for ingredient_id, name in ingredients:
        connection.execute(
            sa.text("UPDATE ingredients SET name = :name WHERE id = :id"),
            {"id": ingredient_id, "name": _title_case(name)},
        )

    recipes = connection.execute(
        sa.text("SELECT id, title FROM recipes WHERE is_staple = 0")
    ).fetchall()
    for recipe_id, title in recipes:
        connection.execute(
            sa.text("UPDATE recipes SET title = :title WHERE id = :id"),
            {"id": recipe_id, "title": _title_case(title)},
        )

    staple_ids = connection.execute(
        sa.text("SELECT id FROM recipes WHERE is_staple = 1 ORDER BY id")
    ).fetchall()
    connection.execute(sa.text("UPDATE recipes SET is_staple = 0"))
    if staple_ids:
        connection.execute(
            sa.text("UPDATE recipes SET is_staple = 1, title = 'Staples' WHERE id = :id"),
            {"id": staple_ids[0][0]},
        )
    else:
        connection.execute(
            sa.text(
                "INSERT INTO recipes "
                "(title, source_url, instructions, servings, created_at, is_planned, is_staple) "
                "VALUES ('Staples', NULL, NULL, NULL, :created_at, 0, 1)"
            ),
            {"created_at": datetime.now(timezone.utc)},
        )

    with op.batch_alter_table("recipes") as batch_op:
        batch_op.alter_column("is_staple", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("recipes") as batch_op:
        batch_op.drop_column("is_staple")