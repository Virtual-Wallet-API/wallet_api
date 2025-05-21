from .routers import root_router

from main import app

app.include_router(root_router)
