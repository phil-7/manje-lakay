from sqlalchemy.orm import Session

from app.models import Ingredient, Recipe, RecipeIngredient
from app.scraper import scrape_recipe_ingredients


def get_or_create_ingredient(db: Session, name: str) -> Ingredient:
    """Reuse an existing ingredient row if one already has this (normalized) name."""
    name = name.strip().lower()
    existing = db.query(Ingredient).filter_by(name=name).first()
    if existing:
        return existing
    return Ingredient(name=name)


def _build_recipe_ingredients_from_entries(
    db: Session, entries: list[dict]
) -> list[RecipeIngredient]:
    """
    Build RecipeIngredient rows from structured entries -- used for manual
    entry, editing, and confirming a scrape. Each entry is a dict with
    "name", and optionally "quantity" and "unit". De-duplicates by name,
    keeping the first occurrence if the same ingredient is listed twice.
    """
    seen_names = set()
    result = []
    for entry in entries:
        name = (entry.get("name") or "").strip().lower()
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        result.append(
            RecipeIngredient(
                ingredient=get_or_create_ingredient(db, name),
                quantity=entry.get("quantity"),
                unit=entry.get("unit"),
            )
        )
    return result


def create_manual_recipe(
    db: Session,
    title: str,
    instructions: str | None,
    servings: int | None,
    ingredients: list[dict],
) -> Recipe:
    """
    Save a recipe the user typed in themselves (not scraped). Ingredients
    are already structured (name/quantity/unit picked via form fields,
    same as editing) -- no free-text parsing involved, which avoids the
    NLP parser guessing wrong on unusual phrasing.

    Raises ValueError if the title is empty or no ingredients are given --
    we don't allow saving an empty/placeholder recipe.
    """
    title = title.strip()
    if not title:
        raise ValueError("Recipe title cannot be empty.")

    if instructions is not None:
        instructions = instructions.strip() or None

    recipe_ingredients = _build_recipe_ingredients_from_entries(db, ingredients)
    if not recipe_ingredients:
        raise ValueError("Recipe must have at least one ingredient.")

    recipe = Recipe(
        title=title,
        source_url=None,
        instructions=instructions,
        servings=servings,
    )
    recipe.recipe_ingredients = recipe_ingredients

    db.add(recipe)
    db.commit()
    return recipe


def preview_scraped_recipe(url: str) -> dict:
    """
    Scrape a URL and return a DRAFT for the user to review/edit before
    anything is saved. Deliberately touches the database not at all --
    not even to look up or create Ingredient rows -- since the user
    might cancel or change things before confirming.

    Raises ValueError if the page has no Recipe JSON-LD, no title, or
    no usable ingredients (same cases as before).
    """
    title, servings, parsed_lines = scrape_recipe_ingredients(url)

    if not title or not title.strip():
        raise ValueError(f"Could not find a recipe title at {url}")
    if not parsed_lines:
        raise ValueError(f"Could not find any usable ingredients at {url}")

    return {
        "title": title.strip(),
        "servings": servings,
        "source_url": url,
        "ingredients": [
            {"name": p.name, "quantity": p.quantity, "unit": p.unit}
            for p in parsed_lines
        ],
    }


def create_recipe_from_confirmed_scrape(
    db: Session,
    title: str,
    instructions: str | None,
    servings: int | None,
    source_url: str | None,
    ingredients: list[dict],
) -> Recipe:
    """
    Save a recipe from a scrape the user has already reviewed and
    possibly corrected. `ingredients` is already structured -- no
    re-parsing here, since the user may have fixed quantities/units
    or added ingredients by hand in the review step.

    Raises ValueError if the title is empty or no ingredients remain.
    """
    title = title.strip()
    if not title:
        raise ValueError("Recipe title cannot be empty.")

    if instructions is not None:
        instructions = instructions.strip() or None

    if source_url is not None:
        source_url = source_url.strip() or None

    recipe_ingredients = _build_recipe_ingredients_from_entries(db, ingredients)
    if not recipe_ingredients:
        raise ValueError("Recipe must have at least one ingredient.")

    recipe = Recipe(
        title=title,
        source_url=source_url,
        instructions=instructions,
        servings=servings,
    )
    recipe.recipe_ingredients = recipe_ingredients

    db.add(recipe)
    db.commit()
    return recipe


def toggle_planned(db: Session, recipe_id: int) -> Recipe:
    """
    Flip a recipe's is_planned flag (on your plan <-> not on your plan).

    Raises ValueError if no recipe with that id exists.
    """
    recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    if recipe is None:
        raise ValueError(f"Recipe {recipe_id} not found")

    recipe.is_planned = not recipe.is_planned
    db.commit()
    return recipe


def update_recipe(
    db: Session,
    recipe_id: int,
    title: str,
    source_url: str | None,
    instructions: str | None,
    servings: int | None,
    ingredients: list[dict],
) -> Recipe:
    """
    Edit an existing recipe's title, source URL, instructions, servings,
    and ingredients. Unlike creation, `ingredients` here is already
    structured (list of {"name", "quantity", "unit"} dicts) -- this is
    for the edit form, where the user adjusts fields directly rather
    than typing a free-text line to be re-parsed.

    The ingredient list is fully REPLACED, not merged. Same validation
    as creating a recipe: title and at least one ingredient required.

    Raises ValueError if the recipe doesn't exist, the title is empty,
    or no ingredients are given.
    """
    recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    if recipe is None:
        raise ValueError(f"Recipe {recipe_id} not found")

    title = title.strip()
    if not title:
        raise ValueError("Recipe title cannot be empty.")

    recipe_ingredients = _build_recipe_ingredients_from_entries(db, ingredients)
    if not recipe_ingredients:
        raise ValueError("Recipe must have at least one ingredient.")

    if instructions is not None:
        instructions = instructions.strip() or None

    if source_url is not None:
        source_url = source_url.strip() or None

    recipe.title = title
    recipe.source_url = source_url
    recipe.instructions = instructions
    recipe.servings = servings
    recipe.recipe_ingredients = recipe_ingredients

    db.commit()
    return recipe


def delete_recipe(db: Session, recipe_id: int) -> None:
    """
    Delete a recipe. Its RecipeIngredient rows (the recipe-specific
    quantity/unit pairings) are deleted automatically via cascade. The
    underlying Ingredient rows are NOT deleted -- they stay in the
    database in case other recipes still reference them.

    Raises ValueError if no recipe with that id exists.
    """
    recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    if recipe is None:
        raise ValueError(f"Recipe {recipe_id} not found")

    db.delete(recipe)
    db.commit()