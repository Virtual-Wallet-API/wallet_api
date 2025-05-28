from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.infrestructure import invalid_credentials, verify_token, SessionLocal, forbidden_access, pending_user, \
    deactivated_user, blocked_user, forced_password_reset
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def getValidUser(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
        Returns an instance of User if the token is valid and the account is not deactivated.
    """
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise invalid_credentials
    if user.status == "deactivated":
        raise deactivated_user
    return user


def get_active_user_except_blocked(user: User = Depends(getValidUser)):
    """
        Return an instance of User - the currently logged-in user if their account status is not blocked.
    """
    if user.status == "blocked":
        raise blocked_user
    if user.status == "pending":
        raise pending_user
    return user


def get_user_except_pending_fpr(user: User = Depends(getValidUser)):
    """
        Return an instance of User - the currently logged-in user if their account status is active
        and do not require forced password reset.
    """
    if user.forced_password_reset:
        raise forced_password_reset
    if user.status == "pending":
        raise pending_user

    return user


def get_user_except_fpr(user: User = Depends(getValidUser)):
    """
        Return an instance of User - the currently logged-in user except those forced to reset their password.
    """
    if user.forced_password_reset:
        raise forced_password_reset

    return user


def get_user_even_with_fpr(user: User = Depends(getValidUser)):
    """
        Return an instance of User - the currently logged-in user even if they're forced to reset their password.
    """
    return user


def get_current_admin(admin: User = Depends(get_active_user_except_blocked)):
    """
        Return the User instance of the logged-in user if they are active, an admin and aren't expected to reset their password.
    """
    if not admin.admin:
        raise forbidden_access
    if admin.forced_password_reset:
        raise forced_password_reset

    return admin
