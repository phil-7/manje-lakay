from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import calendar, grocery, pages, recipes

# Schema creation/updates are handled by Alembic migrations now (see
# alembic/), not by SQLAlchemy's create_all(). Run `alembic upgrade head`
# before starting the app -- on a brand new database this creates every
# table from scratch; on an existing one it applies just what changed.

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