from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.infrestructure.database import SessionLocal
from app.infrestructure.auth import verify_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
