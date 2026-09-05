from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Recipe
from app.recipes import (
    create_manual_recipe,
    create_recipe_from_confirmed_scrape,
    delete_recipe,
    preview_scraped_recipe,
    toggle_planned,
    update_recipe,
)
from app.schemas import (
    ManualRecipeCreate,
    RecipeOut,
    RecipeUpdate,
    ScrapedRecipeConfirm,
    ScrapedRecipeCreate,
    ScrapedRecipePreview,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("/manual", response_model=RecipeOut, status_code=201)
def add_manual_recipe(payload: ManualRecipeCreate, db: Session = Depends(get_db)):
    try:
        recipe = create_manual_recipe(
            db,
            payload.title,
            payload.instructions,
            payload.servings,
            [entry.model_dump() for entry in payload.ingredients],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RecipeOut.from_recipe(recipe)


@router.post("/scrape-preview", response_model=ScrapedRecipePreview)
def preview_scrape(payload: ScrapedRecipeCreate, db: Session = Depends(get_db)):
    """
    Scrapes the URL and returns a draft for the user to review/edit --
    does NOT save anything. The user reviews it in a popup, then either
    confirms (POST /recipes/scrape-confirm) or discards it.
    """
    try:
        return preview_scraped_recipe(payload.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scrape-confirm", response_model=RecipeOut, status_code=201)
def confirm_scrape(payload: ScrapedRecipeConfirm, db: Session = Depends(get_db)):
    """Saves a scraped recipe after the user has reviewed/edited the preview."""
    try:
        recipe = create_recipe_from_confirmed_scrape(
            db,
            payload.title,
            payload.servings,
            payload.source_url,
            [entry.model_dump() for entry in payload.ingredients],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RecipeOut.from_recipe(recipe)


@router.get("", response_model=list[RecipeOut])
def list_recipes(planned: bool | None = None, db: Session = Depends(get_db)):
    """
    List recipes. Pass ?planned=true to get only recipes on your plan,
    or ?planned=false for only the ones that aren't. Omit it entirely
    to get everything.
    """
    query = db.query(Recipe)
    if planned is not None:
        query = query.filter(Recipe.is_planned == planned)
    return [RecipeOut.from_recipe(r) for r in query.all()]


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    if recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")
    return RecipeOut.from_recipe(recipe)


@router.post("/{recipe_id}/toggle-plan", response_model=RecipeOut)
def toggle_recipe_planned(recipe_id: int, db: Session = Depends(get_db)):
    try:
        recipe = toggle_planned(db, recipe_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RecipeOut.from_recipe(recipe)


@router.put("/{recipe_id}", response_model=RecipeOut)
def edit_recipe(recipe_id: int, payload: RecipeUpdate, db: Session = Depends(get_db)):
    try:
        recipe = update_recipe(
            db,
            recipe_id,
            payload.title,
            payload.instructions,
            payload.servings,
            [entry.model_dump() for entry in payload.ingredients],
        )
    except ValueError as e:
        status = 404 if "not found" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))
    return RecipeOut.from_recipe(recipe)


@router.delete("/{recipe_id}", status_code=204)
def remove_recipe(recipe_id: int, db: Session = Depends(get_db)):
    try:
        delete_recipe(db, recipe_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))