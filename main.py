from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import *
from app.business.transaction.transactions_recurring import RecurringService
from app.infrestructure.database import Base, engine
from app.infrestructure.scheduler import init_scheduler
from frontend.routers import root_router

# Ensure the database is not missing tables
Base.metadata.create_all(bind=engine, checkfirst=True)


# Create lifespan event handler for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    scheduler = init_scheduler()
    print("Scheduler started")
    RecurringService.register_recurring_transactions()
    print("Recurring transactions registered")
    try:
        yield
    finally:
        # Shutdown logic
        if scheduler.running:
            scheduler.shutdown()
            print("Scheduler shut down")


# FastAPI app
app = FastAPI(
    title="Virtual Wallet API",
    description="""
    The Virtual Wallet API allows users to register, manage their profile, cards, contacts, and perform transactions such as deposits, withdrawals, and transfers. 
    
    - Register/login/logout
    - Manage credit/debit cards
    - Make deposits and withdrawals
    - Send and receive money
    - Categorize transactions
    - Admin endpoints for user and transaction management
    
    See the [Swagger UI](/docs) for full details and try out the endpoints interactively.
    """,
    version="1.0.0",
    openapi_tags=[{"name": "Virtual Wallet API"}],
    lifespan=lifespan
)

# static files for frontend
app.mount("/static", StaticFiles(directory="frontend/public/static", check_dir=True), name="static")

# Router insertion
prefix = "/api/v1"
app.include_router(admin_router, prefix=prefix + "/admin")
app.include_router(users_router, prefix=prefix + "/users")
app.include_router(cards_router, prefix=prefix + "/cards")
app.include_router(categories_router, prefix=prefix + "/categories")
app.include_router(deposits_router, prefix=prefix + "/deposits")
app.include_router(withdrawals_router, prefix=prefix + "/withdrawals")
app.include_router(transactions_router, prefix=prefix + "/transactions")

# Frontend routes
app.include_router(root_router, tags=["Frontend"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
