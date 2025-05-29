import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.infrestructure.database import Base, engine
from app import *
import frontend.frontend

print("Create all...")
Base.metadata.create_all(bind=engine)

app = FastAPI(openapi_tags=[{"name": "Virtual Wallet API"}])

# static files for frontend
app.mount("/static", StaticFiles(directory="frontend/static", check_dir=True), name="static")

# Router insertion
prefix = "/api/v1"
app.include_router(admin_router, prefix=prefix + "/admin")
app.include_router(users_router, prefix=prefix + "/users")
app.include_router(cards_router, prefix=prefix + "/cards")
app.include_router(categories_router, prefix=prefix + "/categories")
app.include_router(deposits_router, prefix=prefix + "/deposits")
app.include_router(withdrawals_router, prefix=prefix + "/withdrawals")
app.include_router(transactions_router, prefix=prefix + "/transactions")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
