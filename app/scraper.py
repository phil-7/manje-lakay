import json
import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from ingredient_parser import parse_ingredient


@dataclass
class ParsedIngredientLine:
    name: str
    quantity: float | None
    unit: str | None


# The parser returns full English unit words ("tablespoon", "teaspoon",
# "pound"...), but our dropdown (app/static/ingredient-fields.js) and
# most people's everyday cooking vocabulary use abbreviations. Without
# this, "tablespoon" would never match the "tbsp" option in the UI and
# would always fall through to the free-text "Other" field.
UNIT_ALIASES = {
    "tablespoon": "tbsp", "tablespoons": "tbsp",
    "teaspoon": "tsp", "teaspoons": "tsp",
    "cups": "cup",
    "fluid_ounce": "fl oz", "fluid_ounces": "fl oz", "fluid ounce": "fl oz",
    "pints": "pint",
    "quarts": "quart",
    "gallons": "gallon",
    "milliliter": "ml", "milliliters": "ml", "millilitre": "ml",
    "liter": "l", "liters": "l", "litre": "l",
    "gram": "g", "grams": "g",
    "kilogram": "kg", "kilograms": "kg",
    "ounce": "oz", "ounces": "oz",
    "pound": "lb", "pounds": "lb", "lbs": "lb",
    "sprigs": "sprig",
    "cloves": "clove",
    "pinches": "pinch",
    "slices": "slice",
    "stalks": "stalk",
    "cans": "can",
    "sticks": "stick",
}


def normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return unit
    return UNIT_ALIASES.get(unit.strip().lower(), unit.strip().lower())


def fetch_page(url: str) -> str:
    """Fetch the raw HTML of a recipe page."""
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    response.raise_for_status()
    return response.text


def _flatten_json_ld(data):
    """
    JSON-LD blocks can be a single object, a list of objects, or wrapped
    in an "@graph" list. This walks all three shapes and yields every
    individual object found, so we can search them for a Recipe.
    """
    if isinstance(data, list):
        for item in data:
            yield from _flatten_json_ld(item)
    elif isinstance(data, dict):
        if "@graph" in data:
            yield from _flatten_json_ld(data["@graph"])
        else:
            yield data


def _is_recipe(node: dict) -> bool:
    node_type = node.get("@type")
    if isinstance(node_type, list):
        return "Recipe" in node_type
    return node_type == "Recipe"


def extract_recipe_json_ld(html: str) -> dict | None:
    """
    Find the schema.org Recipe block embedded in a page's JSON-LD.
    Returns the parsed dict, or None if the page has no Recipe markup.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string)
        except (json.JSONDecodeError, TypeError):
            continue
        for node in _flatten_json_ld(data):
            if _is_recipe(node):
                return node
    return None


def extract_servings(recipe_json_ld: dict) -> int | None:
    """
    Pull a best-effort serving count out of the JSON-LD "recipeYield"
    field. This field is formatted wildly inconsistently across sites --
    sometimes a bare number ("4"), sometimes a phrase ("Serves 6-8",
    "Makes 12 cookies"), sometimes a list of alternates. We just grab
    the first whole number we find, and give up (return None) if there
    isn't one -- this is meant to save typing, not be authoritative.
    """
    yield_value = recipe_json_ld.get("recipeYield")
    if isinstance(yield_value, list):
        yield_value = yield_value[0] if yield_value else None
    if yield_value is None:
        return None

    match = re.search(r"\d+", str(yield_value))
    return int(match.group()) if match else None


def parse_ingredient_line(raw_line: str) -> ParsedIngredientLine | None:
    """
    Parse one raw ingredient line (e.g. "8 oz rice noodles") into a
    structured name/quantity/unit, using a small local NLP model (no
    external API calls, no cost). This is shared by both the scraper
    and manual recipe entry, so both go through identical parsing.

    Returns None if the parser couldn't identify a name at all.

    This is deliberately defensive: some lines are vague enough that the
    parser returns a descriptive word instead of an actual number for
    quantity (e.g. "a few good shakes of cayenne pepper" -> quantity
    literally equals the string "few"). Rather than crash on that, we
    just leave quantity/unit blank for the user to fill in during review.
    """
    try:
        result = parse_ingredient(raw_line)
    except Exception:
        # The parser itself failed outright (rare) -- fall back to using
        # the whole line as the name, with no amount.
        name = raw_line.strip().lower()
        return ParsedIngredientLine(name=name, quantity=None, unit=None) if name else None

    if not result.name:
        return None

    name = result.name[0].text.strip().lower()
    quantity = None
    unit = None
    if result.amount:
        amount = result.amount[0]
        try:
            if amount.quantity is not None:
                quantity = float(amount.quantity)
        except (ValueError, TypeError):
            quantity = None
        if amount.unit is not None:
            unit = normalize_unit(str(amount.unit))

    return ParsedIngredientLine(name=name, quantity=quantity, unit=unit)


def scrape_recipe_ingredients(
    url: str,
) -> tuple[str | None, int | None, list[ParsedIngredientLine]]:
    """
    Full pipeline for one recipe URL:
      1. fetch the page
      2. pull the raw ingredient lines (and serving count) out of its JSON-LD
      3. parse each line into name/quantity/unit

    Returns (recipe_title_or_None, servings_or_None, parsed_ingredient_lines),
    de-duplicated by name and in the order first encountered.

    Raises ValueError if the page has no Recipe JSON-LD at all -- this
    is the "JSON-LD parsing failed" case we'd eventually want a
    fallback for.
    """
    html = fetch_page(url)
    recipe_json_ld = extract_recipe_json_ld(html)
    if recipe_json_ld is None:
        raise ValueError(f"No recipe JSON-LD found at {url}")

    title = recipe_json_ld.get("name")
    servings = extract_servings(recipe_json_ld)
    raw_lines = recipe_json_ld.get("recipeIngredient", [])

    parsed_lines = []
    seen_names = set()
    for line in raw_lines:
        parsed = parse_ingredient_line(line)
        if parsed and parsed.name not in seen_names:
            parsed_lines.append(parsed)
            seen_names.add(parsed.name)

    return title, servings, parsed_lines