from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.models import User

not_exist = HTTPException(status_code=400, detail="User with these details does not exist")


def check_username(username: str, db: Session):
    try:
        return validate_username_exists(username, db)
    except HTTPException:
        return False


def check_id(uid: int, db: Session):
    try:
        return validate_id_exists(uid, db)
    except HTTPException:
        return False


def check_email(email: str, db: Session):
    try:
        return validate_email_exists(email, db)
    except HTTPException:
        return False


def check_phone(phone: str, db: Session):
    try:
        return validate_phone_exists(phone, db)
    except HTTPException:
        return False


def validate_username_exists(username: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if user:
        return user
    raise not_exist


def validate_id_exists(uid: int, db: Session):
    user = db.query(User).filter(User.id == uid).first()
    if user:
        return user
    raise not_exist


def validate_email_exists(email: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    raise not_exist


def validate_phone_exists(phone: int, db: Session):
    user = db.query(User).filter(User.phone_number == phone).first()
    if user:
        return user
    raise not_exist
