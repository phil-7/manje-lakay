from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(include_in_schema=False)  # these are pages, not API endpoints
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def planner_page(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"active_page": "planner"}
    )


@router.get("/add")
def add_page(request: Request):
    return templates.TemplateResponse(
        request, "add.html", {"active_page": "add"}
    )


@router.get("/grocery")
def grocery_page(request: Request):
    return templates.TemplateResponse(
        request, "grocery.html", {"active_page": "grocery"}
    )


@router.get("/all-recipes")
def all_recipes_page(request: Request):
    return templates.TemplateResponse(
        request, "recipes.html", {"active_page": "all-recipes"}
    )