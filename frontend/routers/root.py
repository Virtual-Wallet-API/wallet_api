from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse

from frontend.jinja import templates

router = APIRouter()


@router.get("/", response_model=None)
def read_root(request: Request):
    data = {"request": request,
            "page": "index"}
    return templates.TemplateResponse("index.html", data)


@router.get("/overview", response_model=None)
def read_overview(request: Request):
    data = {"request": request,
            "page": "overview"}
    return templates.TemplateResponse("overview.html", data)


@router.get("/transactions", response_model=None)
def read_transactions(request: Request):
    data = {"request": request,
            "page": "transactions"}
    return templates.TemplateResponse("payments/transactions.html", data)


@router.get("/logout", response_model=None)
def read_logout(request: Request):
    return RedirectResponse("/")
