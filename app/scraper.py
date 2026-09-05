import json

import requests
from bs4 import BeautifulSoup
from ingredient_parser import parse_ingredient


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


def clean_ingredient_name(raw_line: str) -> str | None:
    """
    Turn a raw ingredient line like "8 oz rice noodles" into just the
    core ingredient name, e.g. "rice noodles", using a small local
    NLP model (no external API calls, no cost).

    Returns None if the parser couldn't identify a name at all.
    """
    result = parse_ingredient(raw_line)
    if not result.name:
        return None
    return result.name[0].text.strip().lower()


def scrape_recipe_ingredients(url: str) -> tuple[str | None, list[str]]:
    """
    Full pipeline for one recipe URL:
      1. fetch the page
      2. pull the raw ingredient lines out of its JSON-LD
      3. clean each line down to just the core ingredient name

    Returns (recipe_title_or_None, list_of_clean_ingredient_names),
    de-duplicated and in the order first encountered.

    Raises ValueError if the page has no Recipe JSON-LD at all -- this
    is the "JSON-LD parsing failed" case we'd eventually want a
    fallback for.
    """
    html = fetch_page(url)
    recipe_json_ld = extract_recipe_json_ld(html)
    if recipe_json_ld is None:
        raise ValueError(f"No recipe JSON-LD found at {url}")

    title = recipe_json_ld.get("name")
    raw_lines = recipe_json_ld.get("recipeIngredient", [])

    cleaned_names = []
    seen = set()
    for line in raw_lines:
        name = clean_ingredient_name(line)
        if name and name not in seen:
            cleaned_names.append(name)
            seen.add(name)

    return title, cleaned_names