from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import Recipe


def build_grocery_list(db: Session, recipe_ids: list[int]) -> list[dict]:
    """
    Given the recipe IDs a user has picked, return one entry per unique
    ingredient (de-duplicated across all selected recipes), each listing
    which recipe(s) it belongs to -- e.g. for the "small text below" UI.

    Returns a list of dicts, sorted alphabetically by ingredient name:
        [{"ingredient": "garlic", "recipes": ["Pad Thai", "Garlic Bread"]}, ...]
    """
    recipes = db.query(Recipe).filter(Recipe.id.in_(recipe_ids)).all()

    ingredient_to_recipes = defaultdict(set)
    for recipe in recipes:
        for ingredient in recipe.ingredients:
            ingredient_to_recipes[ingredient.name].add(recipe.title)

    return [
        {"ingredient": name, "recipes": sorted(titles)}
        for name, titles in sorted(ingredient_to_recipes.items())
    ]