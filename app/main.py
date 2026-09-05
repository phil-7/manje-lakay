from fastapi import FastAPI

from app.database import Base, engine
from app.routers import grocery, recipes

# Creates any tables that don't exist yet. Safe to call every startup --
# it does nothing to tables that are already there.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Manje Lakay")

app.include_router(recipes.router)
app.include_router(grocery.router)