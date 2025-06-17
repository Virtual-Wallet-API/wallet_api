from typing import Dict

import fastapi.responses
import requests
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
    data = {"request": request, "page": "account overview"}
    return templates.TemplateResponse("overview.html", data)


@router.get("/reset-password", response_model=None)
def reset_password_page(request: Request):
    data = {"request": request, "page": "reset password"}
    return templates.TemplateResponse("reset_password.html", data)


@router.get("/cards", response_model=None)
def cards(request: Request):
    data = {
        "request": request,
        "page": "cards"
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
    return templates.TemplateResponse("payments/deposits_history.html", {"request": request})


@router.get("/profile", response_model=None)
def profile_settings(request: Request):
    data = {"request": request, "page": "profile settings"}
    return templates.TemplateResponse("profile.html", data)


@router.get("/security", response_model=None)
def security_settings(request: Request):
    data = {"request": request, "page": "security settings"}
    return templates.TemplateResponse("security.html", data)


@router.get("/verify/{email_key}", response_model=None)
def verify_email(request: Request, email_key=str):
    response = requests.put(url=f"{request.base_url}/api/v1/users/email/{email_key}")
    if response.status_code == 200:
        return RedirectResponse(url="/#login-email")
    else:
        return RedirectResponse(url="/#login-email-error")
