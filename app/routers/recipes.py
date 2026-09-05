from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Recipe
from app.recipes import (
    create_manual_recipe,
    create_scraped_recipe,
    delete_recipe,
    toggle_planned,
    update_recipe,
)
from app.schemas import ManualRecipeCreate, RecipeOut, RecipeUpdate, ScrapedRecipeCreate

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("/manual", response_model=RecipeOut, status_code=201)
def add_manual_recipe(payload: ManualRecipeCreate, db: Session = Depends(get_db)):
    try:
        return create_manual_recipe(
            db, payload.title, payload.instructions, payload.ingredient_names
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scrape", response_model=RecipeOut, status_code=201)
def add_scraped_recipe(payload: ScrapedRecipeCreate, db: Session = Depends(get_db)):
    try:
        return create_scraped_recipe(db, payload.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[RecipeOut])
def list_recipes(planned: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Recipe)
    if planned is not None:
        query = query.filter(Recipe.is_planned == planned)
    return query.all()


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    if recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")
    return recipe


@router.post("/{recipe_id}/toggle-plan", response_model=RecipeOut)
def toggle_recipe_planned(recipe_id: int, db: Session = Depends(get_db)):
    try:
        return toggle_planned(db, recipe_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{recipe_id}", response_model=RecipeOut)
def edit_recipe(recipe_id: int, payload: RecipeUpdate, db: Session = Depends(get_db)):
    try:
        return update_recipe(
            db, recipe_id, payload.title, payload.instructions, payload.ingredient_names
        )
    except ValueError as e:
        status = 404 if "not found" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))


@router.delete("/{recipe_id}", status_code=204)
def remove_recipe(recipe_id: int, db: Session = Depends(get_db)):
    try:
        delete_recipe(db, recipe_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
