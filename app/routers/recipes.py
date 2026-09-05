from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Recipe
from app.recipes import create_manual_recipe, create_scraped_recipe
from app.schemas import ManualRecipeCreate, RecipeOut, ScrapedRecipeCreate

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
def list_recipes(db: Session = Depends(get_db)):
    return db.query(Recipe).all()


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    if recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")
    return recipe