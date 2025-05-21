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


@router.get("/cards", response_model=None)
def read_cards(request: Request):
    data = {
        "request": request,
        "page": "cards",
        "debit_cards": [
            {"id": 1, "last_four": 1234, "expiry": "01/23", "balance": "1000.00$", "color": "purple", "status": "active"},
            {"id": 2, "last_four": 1234, "expiry": "01/23", "balance": "1000.00$", "color": "blue",
             "status": "active"},
            {"id": 3, "last_four": 1234, "expiry": "01/23", "balance": "1000.00$", "color": "green",
             "status": "active"},
            {"id": 4, "last_four": 1234, "expiry": "01/23", "balance": "1000.00$", "color": "green",
             "status": "terminated"},
        ],
        "credit_cards": [
            {"id": 5, "last_four": 1234, "expiry": "01/23", "balance": "1000.00$", "color": "red", "status": "expired"},
            {"id": 6, "last_four": 1234, "expiry": "01/23", "balance": "1000.00$", "color": "red",
             "status": "terminated"},
            {"id": 7, "last_four": 1234, "expiry": "01/23", "balance": "1000.00$", "color": "blue", "status": "lost"},
            {"id": 8, "last_four": 1234, "expiry": "01/23", "balance": "1000.00$", "color": "purple",
             "status": "frozen"},
        ]
    }
    return templates.TemplateResponse("cards.html", data)


@router.get("/transactions", response_model=None)
def read_transactions(request: Request):
    data = {"request": request,
            "page": "transactions"}
    return templates.TemplateResponse("payments/transactions.html", data)


@router.get("/deposit", response_model=None)
def read_transactions(request: Request):
    data = {"request": request,
            "page": "deposit"}
    return templates.TemplateResponse("payments/deposit.html", data)


# @router.get("/logout", response_model=None)
# def read_logout(request: Request):
#     return RedirectResponse("/")
