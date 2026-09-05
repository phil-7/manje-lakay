from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.calendar import (
    add_calendar_entry,
    get_calendar_view,
    remove_calendar_entry,
    start_new_calendar,
)
from app.database import get_db
from app.schemas import AddCalendarEntryRequest, CalendarViewOut, StartCalendarRequest

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("", response_model=CalendarViewOut)
def view_calendar(db: Session = Depends(get_db)):
    return get_calendar_view(db)


@router.post("/start", response_model=CalendarViewOut)
def start_calendar(payload: StartCalendarRequest, db: Session = Depends(get_db)):
    try:
        start_new_calendar(db, payload.length_weeks)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return get_calendar_view(db)


@router.post("/entries", status_code=201)
def add_entry(payload: AddCalendarEntryRequest, db: Session = Depends(get_db)):
    try:
        add_calendar_entry(db, payload.date, payload.meal_slot, payload.recipe_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return get_calendar_view(db)


@router.delete("/entries/{entry_id}", status_code=204)
def remove_entry(entry_id: int, db: Session = Depends(get_db)):
    try:
        remove_calendar_entry(db, entry_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))