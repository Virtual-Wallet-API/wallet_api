from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User

not_exist = HTTPException(status_code=400, detail="User with these details does not exist")


class UserValidators:
    UniqueValidation: tuple = ("username", "email", "phone_number")

    @staticmethod
    def search_user_by_identifier(db: Session, identifier: str | int) -> User | None:
        """
        Search a user by their identifier (id, username, email or phone number).
        :param db: The database session.
        :param identifier: The identifier to search for.
        :return: The user object if found, otherwise returns False.
        """
        identifier_map = {
            "id": int,
            "username": str,
            "email": str,
            "phone_number": str
        }

        user = None
        for field, value in identifier_map.items():
            if not isinstance(identifier, value):
                continue

            user = UserValidators.find_user_with(field, identifier, db)
            print("Tested: ", field, identifier)
            print("===")
            if user:
                return user

        raise HTTPException(status_code=400, detail="User with these details does not exist")

    @staticmethod
    def find_user_with(field: str, value: str | int, db: Session) -> User | bool:
        """
        Check if a user exists in the database based on a specific field and value.
        :param field: The field to search for the user (e.g., username, email).
        :param value: The value corresponding to the field to be checked for the user.
        :param db: The database session used to perform the user verification query.
        :return: The `User` object if the user is found, otherwise returns `False`.
        """
        try:
            return UserValidators.find_user_with_or_raise_exception(field, value, db)
        except Exception:
            db.rollback()
            return False

    @staticmethod
    def find_user_with_or_raise_exception(field: str, value: str | int, db: Session, exc: Exception = None) -> User:
        """
        Returns a user matching the given field and value or raises exception 400 if not found.
        :param field: The database field to search for.
        :param value: The value to search for.
        :param db: The database session.
        :param exception: An exception to raise if the user is not found
        :return: User object or raises an exception.
        """
        fields = {
            "username": User.username,
            "email": User.email,
            "phone_number": User.phone_number,
            "id": User.id
        }

        if field not in fields:
            raise ValueError(f"Invalid field '{field}' provided for validate_user_exists_from function.")

        user: Optional[User] = db.query(User).filter(fields[field] == value).first()
        if user:
            return user

        if exc:
            raise exc
        raise not_exist

    @staticmethod
    def validate_unique_user_data(data: dict, db: Session) -> User | bool:
        """
        Validates user data and returns the user object if username, email or phone number is taken.
        :param data: The user data to be validated.
        :param db: The database session.
        :return: User object if user with such credentials exists, otherwise returns False.
        """
        for field, value in data.items():
            if field not in UserValidators.UniqueValidation:
                continue

            user = UserValidators.find_user_with(field, value, db)
            if user:
                return user

        return False
