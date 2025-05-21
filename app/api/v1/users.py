from typing import List

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.business.user.auth import login_service, registration_service
from app.dependencies import get_db
from app.schemas.user import UserCreate, UserPublicResponse
from app.schemas.contact import ContactResponse, ContactPublicResponse

router = APIRouter(tags=["Users"])


@router.post("/", response_model=UserPublicResponse)
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
    return registration_service(user, db)


@router.post("/token", response_model=dict)
def login(user: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Handles user login and token generation.

    This endpoint is responsible for authenticating a user by verifying the
    provided credentials. Upon successful authentication, it generates and
    returns an access token for the user. It utilizes dependency injection
    to process user input and interact with the database session.

    :param user: A form containing the user's credentials.
        The form should include a username and a password.
    :param db: A database session used to validate user credentials and
        retrieve user information.
    :return: Access token generated for the authenticated user.
    :rtype: dict
    """
    return login_service(db, user)


@router.get("/contacts", response_model=List[ContactPublicResponse])
def get_contacts(user: ContactResponse = Depends(get_db)):
    """
    Retrieve a list of contacts associated with the authenticated user.
    """
    return [*user.contacts]
