from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.infrestructure import invalid_credentials, verify_token, SessionLocal, forbidden_access
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


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
    return user


def get_current_admin(admin: User = Depends(get_current_user)):
    """
        Return the User instance of the logged-in user if they are an admin.
    """
    if not admin.admin:
        raise forbidden_access
    return admin