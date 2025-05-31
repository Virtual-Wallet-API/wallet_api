from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from app.business import UAuth, UVal
from app.business.user.user_contacts import UserContacts
from app.dependencies import get_db, get_user_except_pending_fpr, get_user_except_fpr, get_user_even_with_fpr, \
    get_current_admin
from app.models import User, Contact
from app.schemas.contact import ContactResponse, ContactPublicResponse, ContactCreate
from app.schemas.user import UserCreate, UserPublicResponse, UserResponse, UserUpdate

router = APIRouter(tags=["Users"])


@router.post("/", response_model=UserPublicResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user in the database.

    Parameters
    ----------
    user : UserCreate
        User details based on the `UserCreate` schema.
    db : Session (automatically fetched)
        Database session for performing operations.

    Returns
    -------
    UserPrivateResponse
        Newly created user based on the `UserPrivateResponse` schema, excluding the `balance` field.
    """
    return UAuth.register(user, db)


@router.patch("/", response_model=UserPublicResponse,
              description="Update user details - phone, email, password and avatar")
def update_user(update_data: UserUpdate,
                db: Session = Depends(get_db),
                user: User = Depends(get_user_even_with_fpr)):
    """
    Update user details, including phone, email, password, and avatar. This endpoint
    allows authorized clients to modify specific attributes of the current user
    in the system.

    :param update_data: An instance of `UserUpdate` containing the new data
        to update the user with.
    :param db: The database session used to perform database operations.
    :param user: The authenticated user object for whom the update will be performed.
    :return: The updated user information.
    """
    return UAuth.update_user(db, user, update_data)


@router.post("/token", response_model=None)
def login(user: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Verifies user login credentials and returns an access token if successful.

    Parameters
    ----------
    user : OAuth2 credentials (automatically fetched)
        User login credentials based on the `OAuth2PasswordRequestForm` schema.
    db : Session (automatically fetched)
        Database session for performing operations.

    Returns
    -------
    response : Dict
        A dictionary containing the access token, token type and username.
    """
    return UAuth.login(db, user)


@router.get("/me", response_model=UserResponse)
def get_user(user: User = Depends(get_user_except_fpr)):
    """
    Retrieves user details based on the provided access token if the user isn't forced to reset password.

    Parameters
    ----------
    user : Current logged in user (automatically fetched)
        User details based on the `UserResponse` schema.
    db : Session (automatically fetched)
        Database session for performing operations.

    Returns
    -------
    user : UserResponse
        A response containing the user details.
    """
    return user


@router.get("/contacts", response_model=List[ContactPublicResponse])
def get_contacts(db: ContactResponse = Depends(get_db), user: User = Depends(get_user_except_pending_fpr)):
    """
    Retrieve a list of contacts associated with the authenticated user.
    """
    return [*user.contacts]


@router.post("/contacts", response_model=ContactPublicResponse)
def create_contact(contact: ContactCreate,
                   db: Session = Depends(get_db),
                   user: User = Depends(get_user_except_pending_fpr)):
    """
    Creates a new contact for the authenticated user.
    """

    return UserContacts.add_contact(db, user, contact)


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_contact(contact_id: int,
                   db: Session = Depends(get_db),
                   user: User = Depends(get_user_except_pending_fpr)):
    """
    Removes a contact from the authenticated user's list of contacts.
    """
    return UserContacts.remove_contact(db, user, contact_id)