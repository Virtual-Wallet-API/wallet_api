from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import User
from app.schemas import UserPrivateResponse, UserCreate

router = APIRouter(tags=["users"])


@router.post("/", response_model=UserPrivateResponse, response_model_exclude={"balance"})
def create_user(user: UserCreate,
                db: Session = Depends(get_db)):
    """
    Handles the test creation of a new user in the database.

    This function accepts user input data, maps it to the database
    user model, and persists the new user record in the database.
    It uses dependency injection to get a database session.

    :param user: The user details required to create a
                 new user, based on the `UserCreate` schema.
    :param db: The database session used for performing
               the database operations.

    :return: The newly created user based on the
             `UserPrivateResponse` schema.
    """
    user = User(**user.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
