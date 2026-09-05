from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.grocery import build_grocery_list
from app.schemas import GroceryListItem, GroceryListRequest

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