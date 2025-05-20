from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates

from main import app

templates_dir = "frontend/templates"
templates = Jinja2Templates(directory=templates_dir)

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/overview")
def read_root(request: Request):
    return templates.TemplateResponse("overview.html", {"request": request})