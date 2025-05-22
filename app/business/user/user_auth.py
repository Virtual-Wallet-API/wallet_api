from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.infrestructure import generate_token
from app.models import User
from app.schemas.user import UserCreate


# TODO hash passwords
def registration_service(user: UserCreate, db: Session):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def login_service(db: Session, user: OAuth2PasswordRequestForm = Depends()):
    exc = HTTPException(status_code=400, detail="Incorrect username or password")

    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise exc

    # if not pwd_context.verify(db_user.hashed_password, user.password):
    if not db_user.hashed_password == user.password:
        raise exc

    return {"access_token": generate_token(db_user.username), "token_type": "Bearer"}
