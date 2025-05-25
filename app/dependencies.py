from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.infrestructure import invalid_credentials, verify_token, SessionLocal, forbidden_access, pending_user, \
    deactivated_user, blocked_user
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
        Return an instance of User - the currently logged-in user.
    """
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise invalid_credentials
    if user.status == "blocked":
        raise blocked_user
    return user


def get_current_active_user(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
        Return the User instance of the logged-in user if they are active.
    """
    if user.status == "pending":
        raise pending_user
    elif user.status == "deactivated":
        raise deactivated_user
    return user


def get_current_admin(admin: User = Depends(get_current_user)):
    """
        Return the User instance of the logged-in user if they are an admin.
    """
    if not admin.admin:
        raise forbidden_access
    return admin