from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import calendar, grocery, pages, recipes

# Creates any tables that don't exist yet. Safe to call every startup --
# it does nothing to tables that are already there.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Manje Lakay")

# Kept even though the frontend is now served by this same app -- harmless,
# and protects you if you ever serve pages from a different origin later.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipes.router)
app.include_router(grocery.router)
app.include_router(calendar.router)
app.include_router(pages.router)

# Only CSS/JS live here now -- the HTML itself is rendered by pages.py via
# Jinja2 templates, not served as static files anymore.
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")