import uvicorn
from fastapi import FastAPI
from app.infrestructure.database import Base, engine
from app.api.v1.users import router as users_router
from app.api.v1.cards import router as cards_router
import frontend.frontend

print("Create all...")
Base.metadata.create_all(bind=engine)

app = FastAPI(openapi_tags=[{"name": "Virtual Wallet API"}])

# Router insertion
prefix = "/api/v1"
app.include_router(users_router, prefix=prefix + "/users")
app.include_router(cards_router, prefix=prefix + "/cards")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
