from typing import Optional

from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.models import User

not_exist = HTTPException(status_code=400, detail="User with these details does not exist")


def check_user_with(field: str, value: str | int, db: Session) -> User | bool:
    try:
        return validate_user_exists_from(field, value, db)
    except HTTPException:
        return False


def validate_user_exists_from(field: str, value: str | int, db: Session) -> User:
    """
    Returns a user matching the given field and value or raises exception 400 if not found.
    :param field: The database field to search for.
    :param value: The value to search for.
    :param db: The database session.
    :return: User object or raises an exception.
    """
    fields = {
        "username": User.username,
        "email": User.email,
        "phone": User.phone_number,
        "id": User.id
    }

    if field not in fields:
        raise ValueError("Invalid field provided for validate_user_exists_from function.")

    user: Optional[User] = db.query(User).filter(fields[field] == value).first()
    if user:
        return user

    raise not_exist
