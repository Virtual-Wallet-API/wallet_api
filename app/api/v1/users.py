from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import User, Card
from app.schemas import UserPrivateResponse, UserCreate

router = APIRouter(tags=["users"])


@router.post("/", response_model=UserPrivateResponse, response_model_exclude={"balance"})
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user in the database.

    Parameters
    ----------
    user : UserCreate
        User details based on the `UserCreate` schema.
    db : Session
        Database session for performing operations.

    Returns
    -------
    UserPrivateResponse
        Newly created user based on the `UserPrivateResponse` schema, excluding the `balance` field.
    """
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
