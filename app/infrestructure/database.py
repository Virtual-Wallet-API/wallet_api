from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import DB_URL

# url = "sqlite:///./database.db"
url = DB_URL
engine = create_engine(url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@event.listens_for(engine, "handle_error")
def handle_db_error(context):
    print(f"Database error: {str(context.original_exception)}")
    raise HTTPException(status_code=500, detail="Database error occurred")
