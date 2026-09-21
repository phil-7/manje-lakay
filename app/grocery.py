from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import CustomGrocery, Recipe
from app.units import unit_family


def build_grocery_list(db: Session, recipe_ids: list[int]) -> list[dict]:
    """
    Given the recipe IDs a user has picked, return one entry per unique
    ingredient (de-duplicated by name across all selected recipes), each
    listing which recipe(s) it belongs to along with that recipe's
    quantity/unit for it.

    IMPORTANT: amounts are never summed or converted, even when they're
    the same unit type (e.g. two recipes both in tbsp) -- that's a
    deliberately deferred feature. Each recipe's amount is shown
    separately. "mixed_units" is set to True when the amounts for an
    ingredient use genuinely incompatible unit types (e.g. tbsp vs. lb),
    as a heads-up that combining them isn't something we've attempted.

    Returns a list of dicts, sorted alphabetically by ingredient name:
        [{"ingredient": "garlic",
          "entries": [{"recipe": "Pad Thai", "quantity": 2.0, "unit": "clove"}, ...],
          "mixed_units": False}, ...]
    """
    recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()

    grouped = defaultdict(list)
    for recipe in recipes:
        for ri in recipe.recipe_ingredients:
            grouped[ri.ingredient.name].append(
                {"recipe": recipe.title, "quantity": ri.quantity, "unit": ri.unit}
            )

    items = []
    for name in sorted(grouped):
        entries = grouped[name]
        families = {unit_family(entry["unit"]) for entry in entries}
        items.append(
            {
                "ingredient": name,
                "entries": entries,
                "mixed_units": len(families) > 1,
            }
        )
    return items


def list_custom_groceries(db: Session) -> list[CustomGrocery]:
    return db.query(CustomGrocery).order_by(CustomGrocery.name.asc()).all()


def add_custom_grocery(db: Session, name: str) -> CustomGrocery:
    cleaned_name = " ".join(name.strip().split())
    if not cleaned_name:
        raise ValueError("name must not be empty")

    grocery = CustomGrocery(name=cleaned_name)
    db.add(grocery)
    db.commit()
    db.refresh(grocery)
    return grocery


def remove_custom_grocery(db: Session, grocery_id: int) -> None:
    grocery = db.query(CustomGrocery).filter_by(id=grocery_id).first()
    if grocery is None:
        raise ValueError(f"Custom grocery {grocery_id} not found")
    db.delete(grocery)
    db.commit()