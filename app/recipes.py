from sqlalchemy.orm import Session

from app.models import Recipe, Ingredient
from app.scraper import scrape_recipe_ingredients


def get_or_create_ingredient(db: Session, name: str) -> Ingredient:
    """Reuse an existing ingredient row if one already has this (normalized) name."""
    name = name.strip().lower()
    existing = db.query(Ingredient).filter_by(name=name).first()
    if existing:
        return existing
    return Ingredient(name=name)


def create_manual_recipe(
    db: Session,
    title: str,
    instructions: str | None,
    ingredient_names: list[str],
) -> Recipe:
    """
    Save a recipe the user typed in themselves (not scraped).

    Raises ValueError if the title is empty or no ingredients are given --
    we don't allow saving an empty/placeholder recipe.
    """
    title = title.strip()
    if not title:
        raise ValueError("Recipe title cannot be empty.")

    # Normalize and drop any blank entries (e.g. an empty text field a user
    # left behind), then de-duplicate names within this single submission.
    cleaned_names = {name.strip().lower() for name in ingredient_names if name.strip()}
    if not cleaned_names:
        raise ValueError("Recipe must have at least one ingredient.")

    if instructions is not None:
        instructions = instructions.strip() or None

    recipe = Recipe(title=title, source_url=None, instructions=instructions)
    recipe.ingredients = [get_or_create_ingredient(db, name) for name in cleaned_names]

    db.add(recipe)
    db.commit()
    return recipe


def create_scraped_recipe(db: Session, url: str) -> Recipe:
    """
    Scrape a recipe URL for its title and ingredients, then save it.

    IMPORTANT: instructions are always left as None here. We only ever
    pull ingredients from a scraped page, never instructions -- the
    user has to type those in themselves afterward, for legal reasons.

    Raises ValueError if:
      - the page has no Recipe JSON-LD at all (bubbled up from the scraper)
      - the JSON-LD had no title
      - the JSON-LD had no usable ingredients
    In any of those cases, nothing is saved -- the caller should fall
    back to prompting the user for manual entry.
    """
    title, ingredient_names = scrape_recipe_ingredients(url)

    if not title or not title.strip():
        raise ValueError(f"Could not find a recipe title at {url}")
    title = title.strip()

    cleaned_names = {name.strip().lower() for name in ingredient_names if name.strip()}
    if not cleaned_names:
        raise ValueError(f"Could not find any usable ingredients at {url}")

    recipe = Recipe(title=title, source_url=url, instructions=None)
    recipe.ingredients = [get_or_create_ingredient(db, name) for name in cleaned_names]

    db.add(recipe)
    db.commit()
    return recipe