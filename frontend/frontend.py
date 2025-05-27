from main import app
from .routers import root_router

app.include_router(root_router, tags=["Frontend"], prefix="/fe")
