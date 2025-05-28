from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import JSONResponse, RedirectResponse

from app.business import UAuth, UVal
from app.business.user.user_admin import AdminService
from app.dependencies import get_db, get_active_user, get_password_reset_user, get_pending_user
from app.models import User, Contact
from app.schemas.contact import ContactResponse, ContactPublicResponse, ContactCreate
from app.schemas.user import UserCreate, UserPublicResponse, UserResponse

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
def get_user(user: User = Depends(get_pending_user)):
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
def get_contacts(db: ContactResponse = Depends(get_db), user: User = Depends(get_active_user)):
    """
    Retrieve a list of contacts associated with the authenticated user.
    """
    return [*user.contacts]


@router.post("/contacts", response_model=ContactPublicResponse)
def create_contact(contact: ContactCreate,
                   db: Session = Depends(get_db),
                   user: User = Depends(get_active_user)):
    """
    Creates a new contact for the authenticated user.
    """
    UVal.find_user_with_or_raise_exception("id", contact.contact_id, db)

    db_contact = (db.query(Contact)
                  .filter(Contact.contact_id == contact.contact_id and Contact.user_id == user.id).first())
    if db_contact:
        raise HTTPException(status_code=400, detail="Contact already exists")

    db_contact = Contact(contact_id=contact.contact_id, user_id=user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_contact(contact_id: int,
                   db: Session = Depends(get_db),
                   user: User = Depends(get_active_user)):
    """
    Removes a contact from the authenticated user's list of contacts.
    """
    db_contact = (db.query(Contact)
                  .filter(Contact.contact_id == contact_id and Contact.user_id == user.id).first())
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(db_contact)
    db.commit()
    return status.HTTP_204_NO_CONTENT
