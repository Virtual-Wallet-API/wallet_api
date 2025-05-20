import uvicorn
from fastapi import FastAPI
from app.infrestructure.database import Base, engine
from app.api.v1.users import router as users_router






Base.metadata.create_all(bind=engine)
app = FastAPI()
app.include_router(users_router, prefix="/users")







if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)