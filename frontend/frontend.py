from fastapi import APIRouter
from .routers import root_router

from main import app

front = APIRouter(tags=["Frontend"])

app.include_router(root_router)
