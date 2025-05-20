from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates

from main import app

templates_dir = "frontend/templates"
templates = Jinja2Templates(directory=templates_dir)

@app.get("/")
def read_root(request: Request):
    data = {"request": request,
            "page": "index"}
    return templates.TemplateResponse("index.html", data)

@app.get("/overview")
def read_overview(request: Request):
    data = {"request": request,
            "page": "overview"}
    return templates.TemplateResponse("overview.html", data)

@app.get("/transactions")
def read_transactions(request: Request):
    data = {"request": request,
            "page": "transactions"}
    return templates.TemplateResponse("payments/transactions.html", data)