from typing import List, Dict
import time

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from app.business import UAuth, UVal
from app.business.user.user_contacts import UserContacts
from app.dependencies import get_db, get_user_except_pending_fpr, get_user_except_fpr, get_user_even_with_fpr, \
    get_current_admin, get_active_user_except_blocked, getValidUser
from app.models import User, Contact
from app.schemas.contact import ContactResponse, ContactPublicResponse, ContactCreate
from app.schemas.user import UserCreate, UserPublicResponse, UserResponse, UserUpdate, PasswordResetRequest, PasswordResetConfirm
import cloudinary
import cloudinary.uploader
from app.config import CLOUDINARY_URL, SECRET_KEY, ALGORITHM
from fastapi.responses import JSONResponse
from app.infrestructure import auth
from app.business.utils import NotificationService
from app.business.utils.notification_service import EmailTemplates
import jwt, datetime
from app.business.user.user_auth import UserAuthService
from pydantic import BaseModel

# Initialize Cloudinary (auto-loads from CLOUDINARY_URL)
cloudinary.config()

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


@router.put("/email/{key}", response_model=Dict)
def verify_email(key: str,
                 db: Session = Depends(get_db)):
    return UAuth.verifty_email(db, key)


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


@router.post("/avatar", summary="Upload user profile photo (avatar)")
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(getValidUser)
):
    """
    Upload a user's profile photo (avatar) to Cloudinary.
    """
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid image type. Only JPEG, PNG, GIF, and WEBP are allowed."
        )
    try:
        file.file.seek(0)
        upload_params = {
            "folder": "vwallet/avatars",
            "public_id": f"user_{current_user.id}",
            "overwrite": True,
            "resource_type": "image",
        }
        result = cloudinary.uploader.upload(
            file.file,
            **upload_params
        )
        avatar_url = result.get("secure_url")
        if not avatar_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to get secure URL from Cloudinary response"
            )
        current_user.avatar = avatar_url
        db.commit()
        db.refresh(current_user)
        return {"avatar_url": avatar_url}
    except cloudinary.exceptions.Error as e:
        error_msg = str(e)
        if "Invalid Signature" in error_msg:
            raise HTTPException(
                status_code=500,
                detail="Cloudinary authentication failed. Please check API credentials."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Cloudinary upload failed: {error_msg}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Avatar upload failed: {str(e)}"
        )
    finally:
        file.file.close()

@router.post("/forgot-password", response_model=Dict)
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Initiate a password reset by sending a reset link to the user's email.
    - If the email exists, a reset link is sent.
    - Always returns 200 to avoid leaking which emails are registered.
    """
    return UserAuthService.request_password_reset(db, request.email)

@router.post("/reset-password", response_model=Dict)
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Reset the user's password using a valid reset token.
    - token: The JWT token from the reset link.
    - new_password: The new password to set.
    - Returns 200 on success, 400 on invalid/expired token.
    """
    return UserAuthService.reset_password(db, request.token, request.new_password)