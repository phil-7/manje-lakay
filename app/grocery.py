from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import Recipe
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