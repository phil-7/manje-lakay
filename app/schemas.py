from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


# --- Request bodies (what comes IN from the client) ---

class IngredientEntry(BaseModel):
    """One structured ingredient: name, plus optional quantity/unit. Used
    everywhere a recipe's ingredients are submitted -- manual entry,
    editing, and confirming a scrape -- since all three now use the same
    structured quantity/unit/name fields, not free-text lines."""
    name: str
    quantity: float | None = None
    unit: str | None = None


class ManualRecipeCreate(BaseModel):
    title: str
    instructions: str | None = None
    servings: int | None = None
    ingredients: list[IngredientEntry]


class ScrapedRecipeCreate(BaseModel):
    url: str
    instructions: str | None = None


class GroceryListRequest(BaseModel):
    recipe_ids: list[int]


class ScrapedRecipePreview(BaseModel):
    """A scraped recipe that hasn't been saved yet -- nothing in the
    database is touched until the user confirms it via ScrapedRecipeConfirm."""
    title: str
    instructions: str | None = None
    servings: int | None
    source_url: str
    ingredients: list[IngredientEntry]


class ScrapedRecipeConfirm(BaseModel):
    """What the user actually approved after reviewing/editing the preview."""
    title: str
    instructions: str | None = None
    servings: int | None = None
    source_url: str
    ingredients: list[IngredientEntry]


class RecipeUpdate(BaseModel):
    title: str
    source_url: str | None = None
    instructions: str | None = None
    servings: int | None = None
    ingredients: list[IngredientEntry]


# --- Response bodies (what goes OUT to the client) ---

class RecipeIngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    quantity: float | None
    unit: str | None

    @classmethod
    def from_recipe_ingredient(cls, ri):
        """RecipeIngredient's name lives on the related Ingredient, not
        on RecipeIngredient itself, so this flattens the two together
        for the API response."""
        return cls(name=ri.ingredient.name, quantity=ri.quantity, unit=ri.unit)


class RecipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_url: str | None
    instructions: str | None
    servings: int | None
    created_at: datetime
    is_planned: bool
    is_scheduled: bool
    ingredients: list[RecipeIngredientOut]

    @classmethod
    def from_recipe(cls, recipe):
        return cls(
            id=recipe.id,
            title=recipe.title,
            source_url=recipe.source_url,
            instructions=recipe.instructions,
            servings=recipe.servings,
            created_at=recipe.created_at,
            is_planned=recipe.is_planned,
            is_scheduled=bool(recipe.calendar_entries),
            ingredients=[
                RecipeIngredientOut.from_recipe_ingredient(ri)
                for ri in recipe.recipe_ingredients
            ],
        )


class GroceryListEntry(BaseModel):
    recipe: str
    quantity: float | None
    unit: str | None


class GroceryListItem(BaseModel):
    ingredient: str
    entries: list[GroceryListEntry]
    # True when this ingredient's amounts across recipes use incompatible
    # unit types (e.g. tbsp vs. lb) that can't be safely combined. Amounts
    # are always shown separately, never summed -- see app/units.py.
    mixed_units: bool


# --- Calendar ---

class StartCalendarRequest(BaseModel):
    length_weeks: int


class AddCalendarEntryRequest(BaseModel):
    date: date
    meal_slot: str
    recipe_id: int


class CalendarEntryOut(BaseModel):
    id: int
    recipe_id: int
    recipe_title: str


class CalendarDayOut(BaseModel):
    date: date
    breakfast: CalendarEntryOut | None
    lunch: CalendarEntryOut | None
    dinner: CalendarEntryOut | None


class CalendarViewOut(BaseModel):
    start_date: date
    end_date: date
    length_weeks: int
    days: list[CalendarDayOut]