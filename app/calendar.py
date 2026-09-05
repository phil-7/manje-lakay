from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import CalendarEntry, CalendarSettings, Recipe

VALID_LENGTHS = {1, 2, 4}
MEAL_SLOTS = ["breakfast", "lunch", "dinner"]


def next_sunday(from_date: date) -> date:
    """
    The upcoming Sunday, INCLUDING from_date itself if from_date already
    is a Sunday -- per spec, we don't skip ahead a full week just because
    today happens to be the start day already.
    """
    days_until_sunday = (6 - from_date.weekday()) % 7  # Monday=0 ... Sunday=6
    return from_date + timedelta(days=days_until_sunday)


def get_or_create_settings(db: Session) -> CalendarSettings:
    """
    Returns the current calendar settings, creating a default 1-week
    calendar starting next Sunday if none exists yet (first-ever visit).
    """
    settings = db.query(CalendarSettings).filter_by(id=1).first()
    if settings is None:
        settings = CalendarSettings(id=1, start_date=next_sunday(date.today()), length_weeks=1)
        db.add(settings)
        db.commit()
    return settings


def start_new_calendar(db: Session, length_weeks: int) -> CalendarSettings:
    """
    Wipes every scheduled recipe and starts a fresh calendar of the
    given length, beginning the next Sunday (today, if today is Sunday).
    Does NOT touch any recipe's is_planned flag.

    Raises ValueError if length_weeks isn't one of the supported options.
    """
    if length_weeks not in VALID_LENGTHS:
        raise ValueError(f"length_weeks must be one of {sorted(VALID_LENGTHS)}")

    db.query(CalendarEntry).delete()

    settings = db.query(CalendarSettings).filter_by(id=1).first()
    if settings is None:
        settings = CalendarSettings(id=1)
        db.add(settings)

    settings.start_date = next_sunday(date.today())
    settings.length_weeks = length_weeks
    db.commit()
    return settings


def get_calendar_view(db: Session) -> dict:
    """
    The full current calendar: date range plus every day in it, each
    with its three meal slots (an entry dict, or None if empty).
    """
    settings = get_or_create_settings(db)
    end_date = settings.start_date + timedelta(days=settings.length_weeks * 7 - 1)

    entries = (
        db.query(CalendarEntry)
        .filter(CalendarEntry.date >= settings.start_date, CalendarEntry.date <= end_date)
        .all()
    )
    entries_by_date_slot = {(e.date, e.meal_slot): e for e in entries}

    def entry_out(entry):
        if entry is None:
            return None
        return {"id": entry.id, "recipe_id": entry.recipe_id, "recipe_title": entry.recipe.title}

    days = []
    current = settings.start_date
    while current <= end_date:
        days.append(
            {
                "date": current,
                "breakfast": entry_out(entries_by_date_slot.get((current, "breakfast"))),
                "lunch": entry_out(entries_by_date_slot.get((current, "lunch"))),
                "dinner": entry_out(entries_by_date_slot.get((current, "dinner"))),
            }
        )
        current += timedelta(days=1)

    return {
        "start_date": settings.start_date,
        "end_date": end_date,
        "length_weeks": settings.length_weeks,
        "days": days,
    }


def add_calendar_entry(
    db: Session, entry_date: date, meal_slot: str, recipe_id: int
) -> CalendarEntry:
    """
    Schedule a recipe into a specific day + meal slot. If that slot
    already has a recipe, it's replaced (a slot holds exactly one
    recipe). Also sets the recipe's is_planned flag to True -- this is
    idempotent, so scheduling the same recipe again elsewhere doesn't
    change anything about how it appears on the Plan.

    Raises ValueError if the date is outside the current calendar's
    range, meal_slot isn't valid, or the recipe doesn't exist.
    """
    if meal_slot not in MEAL_SLOTS:
        raise ValueError(f"meal_slot must be one of {MEAL_SLOTS}")

    settings = get_or_create_settings(db)
    end_date = settings.start_date + timedelta(days=settings.length_weeks * 7 - 1)
    if not (settings.start_date <= entry_date <= end_date):
        raise ValueError(
            f"{entry_date} is outside the current calendar range "
            f"({settings.start_date} to {end_date})"
        )

    recipe = db.query(Recipe).filter_by(id=recipe_id).first()
    if recipe is None:
        raise ValueError(f"Recipe {recipe_id} not found")

    existing = (
        db.query(CalendarEntry)
        .filter_by(date=entry_date, meal_slot=meal_slot)
        .first()
    )
    if existing is not None:
        db.delete(existing)
        db.flush()

    entry = CalendarEntry(date=entry_date, meal_slot=meal_slot, recipe_id=recipe_id)
    db.add(entry)

    recipe.is_planned = True

    db.commit()
    return entry


def remove_calendar_entry(db: Session, entry_id: int) -> None:
    """
    Clears one meal slot. Does NOT change the recipe's is_planned flag --
    that stays under the user's manual control via Unplan, since the
    recipe might still be scheduled in another slot.

    Raises ValueError if no entry with that id exists.
    """
    entry = db.query(CalendarEntry).filter_by(id=entry_id).first()
    if entry is None:
        raise ValueError(f"Calendar entry {entry_id} not found")
    db.delete(entry)
    db.commit()