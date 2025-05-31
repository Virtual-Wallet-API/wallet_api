from typing import Dict

from fastapi import APIRouter, Request
from fastapi.params import Depends
from starlette.responses import RedirectResponse

from frontend.jinja import templates
from frontend.services.dependencies import get_valid_user_data

router = APIRouter()


@router.get("/", response_model=None)
def root(request: Request):
    data = {"request": request,
            "page": "VWallet - Home"}
    return templates.TemplateResponse("index.html", data)


@router.get("/account", response_model=None)
def account_overview(request: Request):
    data = {"request": request,
            "page": "account overview"}
    return templates.TemplateResponse("overview.html", data)


@router.get("/cards", response_model=None)
def cards(request: Request):
    data = {
        "request": request,
        "page": "cards",
        "debit_cards": [
            {"id": 1, "last_four": 1234, "expiry": "01/23", "balance": "1000.00$", "color": "purple",
             "status": "active"},
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
def transactions(request: Request):
    data = {"request": request,
            "page": "transactions"}
    return templates.TemplateResponse("payments/transactions.html", data)


@router.get("/send", response_model=None)
def send(request: Request):
    data = {"request": request,
            "page": "send"}
    return templates.TemplateResponse("payments/send.html", data)


@router.get("/receive", response_model=None)
def receive(request: Request):
    data = {"request": request,
            "page": "receive"}
    return templates.TemplateResponse("payments/receive.html", data)


@router.get("/deposits", response_model=None)
def deposit(request: Request):
    data = {"request": request,
            "page": "deposits"}
    return templates.TemplateResponse("payments/deposits.html", data)


@router.get("/withdrawals", response_model=None)
def withdrawal(request: Request):
    data = {"request": request,
            "page": "withdrawals"}
    return templates.TemplateResponse("payments/withdrawals.html", data)


@router.get("/contacts", response_model=None)
def contacts(request: Request):
    data = {"request": request,
            "page": "contacts"}
    return templates.TemplateResponse("contacts.html", data)


@router.get("/logout", response_model=None)
def read_logout(request: Request):
    request.cookies.clear()
    return RedirectResponse("/fe")


@router.get("/authtest", response_model=Dict)
def test_auth_dependency(username: str = Depends(get_valid_user_data)):
    return {"username": username}


@router.get("/all-deposits", response_model=Dict)
def user_deposits_search(request: Request):
    return templates.TemplateResponse("payments/user_deposits.html", {"request": request})
