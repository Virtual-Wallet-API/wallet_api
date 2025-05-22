from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2AuthorizationCodeBearer
from sqlalchemy.orm import Session
from starlette import status

from app.business.user.user_auth import login_service, registration_service
from app.business.user.user_validators import validate_user_exists_from
from app.dependencies import get_db, get_current_user
from app.models import User, Contact
from app.schemas.user import UserCreate, UserPublicResponse
from app.schemas.contact import ContactResponse, ContactPublicResponse, ContactCreate

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
    return login_service(db, user)


@router.get("/contacts", response_model=List[ContactPublicResponse])
def get_contacts(db: ContactResponse = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieve a list of contacts associated with the authenticated user.
    """
    return [*user.contacts]


@router.post("/contacts", response_model=ContactPublicResponse)
def create_contact(contact: ContactCreate,
                   db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    """
    Creates a new contact for the authenticated user.
    """
    validate_user_exists_from("id", contact.contact_id, db)

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
                   user: User = Depends(get_current_user)):
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
