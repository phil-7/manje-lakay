from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.grocery import (
    add_custom_grocery,
    build_grocery_list,
    list_custom_groceries,
    remove_custom_grocery,
)
from app.schemas import (
    CustomGroceryCreate,
    CustomGroceryOut,
    GroceryListItem,
    GroceryListRequest,
)

router = APIRouter(prefix="/grocery-list", tags=["grocery-list"])


@router.post("", response_model=list[GroceryListItem])
def get_grocery_list(payload: GroceryListRequest, db: Session = Depends(get_db)):
    """
    Given a set of recipe IDs, return the combined, de-duplicated
    ingredient list -- each ingredient tagged with which recipe(s) it
    belongs to. IDs that don't match a real recipe are just ignored,
    not treated as an error.
    """
    return build_grocery_list(db, payload.recipe_ids)


@router.get("/custom", response_model=list[CustomGroceryOut])
def get_custom_groceries(db: Session = Depends(get_db)):
    return list_custom_groceries(db)


@router.post("/custom", response_model=CustomGroceryOut, status_code=201)
def create_custom_grocery(payload: CustomGroceryCreate, db: Session = Depends(get_db)):
    try:
        return add_custom_grocery(db, payload.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/custom/{grocery_id}", status_code=204)
def delete_custom_grocery(grocery_id: int, db: Session = Depends(get_db)):
    try:
        remove_custom_grocery(db, grocery_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))