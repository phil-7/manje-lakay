from datetime import datetime

from pydantic import BaseModel, ConfigDict


# --- Request bodies (what comes IN from the client) ---
# These never have an id or created_at -- that data doesn't exist until
# after we save something.

class ManualRecipeCreate(BaseModel):
    title: str
    instructions: str | None = None
    ingredient_names: list[str]


class ScrapedRecipeCreate(BaseModel):
    url: str


class GroceryListRequest(BaseModel):
    recipe_ids: list[int]


# --- Response bodies (what goes OUT to the client) ---
# These mirror the database models, but only expose what's safe/useful
# to send back over the API.

class IngredientOut(BaseModel):
    # Lets pydantic read this straight from a SQLAlchemy Ingredient
    # object's attributes (ingredient.id, ingredient.name) instead of
    # requiring a plain dict.
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class RecipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_url: str | None
    instructions: str | None
    created_at: datetime
    ingredients: list[IngredientOut]


class GroceryListItem(BaseModel):
    ingredient: str
    recipes: list[str]