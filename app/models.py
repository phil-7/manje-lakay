from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.database import Base

# Many-to-many link between recipes and ingredients.
# No "amount" column on purpose -- quantities are out of scope for now.
recipe_ingredients = Table(
    "recipe_ingredients",
    Base.metadata,
    Column("recipe_id", Integer, ForeignKey("recipes.id"), primary_key=True),
    Column("ingredient_id", Integer, ForeignKey("ingredients.id"), primary_key=True),
)


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    # Normalized (lowercased/trimmed) name, so "Garlic" and "garlic"
    # from two different recipes collapse into one row.
    name = Column(String, unique=True, nullable=False, index=True)

    recipes = relationship(
        "Recipe", secondary=recipe_ingredients, back_populates="ingredients"
    )

    def __repr__(self):
        return f"<Ingredient {self.name!r}>"


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

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    ingredients = relationship(
        "Ingredient", secondary=recipe_ingredients, back_populates="recipes"
    )

    def __repr__(self):
        return f"<Recipe {self.title!r}>"