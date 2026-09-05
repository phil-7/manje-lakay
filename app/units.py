VOLUME_UNITS = {
    "tsp", "teaspoon", "teaspoons",
    "tbsp", "tablespoon", "tablespoons",
    "fl_oz", "fluid_ounce", "fluid_ounces",
    "cup", "cups",
    "pint", "pints",
    "quart", "quarts",
    "gallon", "gallons",
    "ml", "milliliter", "milliliters",
    "l", "liter", "liters",
}

WEIGHT_UNITS = {
    "g", "gram", "grams",
    "kg", "kilogram", "kilograms",
    "oz", "ounce", "ounces",
    "lb", "lbs", "pound", "pounds",
}


def unit_family(unit: str | None) -> str:
    """
    Classify a unit as "volume", "weight", or "count" (anything else,
    including no unit at all -- e.g. "2 eggs", "1 bell pepper", or an
    informal unit like "pinch"/"clove" we don't have a conversion for).

    This is used to flag when the SAME ingredient is measured in
    incompatible ways across recipes (e.g. tbsp vs. lb) -- not to
    convert between them. Converting volume <-> weight requires
    ingredient-specific density data we don't have, so we deliberately
    don't attempt it.
    """
    if not unit:
        return "count"
    normalized = unit.strip().lower()
    if normalized in VOLUME_UNITS:
        return "volume"
    if normalized in WEIGHT_UNITS:
        return "weight"
    return "count"