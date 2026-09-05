from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    # Normalized (lowercased/trimmed) name, so "Garlic" and "garlic"
    # from two different recipes collapse into one row.
    name = Column(String, unique=True, nullable=False, index=True)

    def __repr__(self):
        return f"<Ingredient {self.name!r}>"


class RecipeIngredient(Base):
    """
    The link between a Recipe and an Ingredient -- but unlike a plain
    many-to-many table, this is its own real row, because it carries
    data specific to THIS pairing: how much of this ingredient THIS
    recipe uses. The same Ingredient (e.g. "garlic") can be linked to
    many recipes, each with its own quantity/unit.
    """

    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)

    # Both nullable -- plenty of ingredient lines have no clean amount
    # ("cilantro for garnishing") or an informal one we can't convert
    # ("a pinch of salt", unit="pinch").
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)

    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient")

    def __repr__(self):
        return f"<RecipeIngredient {self.quantity} {self.unit} {self.ingredient_id}>"


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)

    # Set only when scraped from the web; NULL for manually-entered recipes.
    source_url = Column(String, nullable=True)

    # IMPORTANT: this is always typed in by the user, never pulled from a
    # scraped page. Any future URL-scraping logic should only ever touch
    # ingredients, not this field -- for legal reasons.
    instructions = Column(Text, nullable=True)

    # Best-effort serving count. Scraped from the page's "recipeYield"
    # when present; typed in manually otherwise. Just a number, not tied
    # to ingredient scaling (yet).
    servings = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Whether this recipe is currently on the "recipes I plan to make" list.
    # A simple flag, not a per-date schedule -- a recipe is either planned
    # or it isn't.
    is_planned = Column(Boolean, default=False, nullable=False)

    recipe_ingredients = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeIngredient.id",
    )

    def __repr__(self):
        return f"<Recipe {self.title!r}>"