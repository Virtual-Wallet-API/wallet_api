from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import JSONResponse

from app.business.user.user_validators import UserValidators as UVal, UserValidators
from app.dependencies import get_db
from app.infrestructure import generate_token, data_validators, auth, DataValidators
from app.models import User, UStatus
from app.schemas.user import UserCreate, UserUpdate


class UserAuthService:
    """Business logic for user authentication and authorization"""

    # TODO hash passwords
    @classmethod
    def register(cls, user_data: UserCreate, db: Session) -> User:
        """
        Create a new user account in the database.
        :param user_data: user input data
        :param db: database session
        :return user: User object if account is successfully created
        """
        user = UVal.validate_unique_user_data(dict(user_data), db)
        if user:
            raise HTTPException(status_code=400, detail="Username, email or phone number is already in use")

        user = User(username=user_data.username,
                    hashed_password=user_data.password,
                    email=user_data.email,
                    phone_number=user_data.phone_number)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def login(cls,
              db: Session = Depends(get_db),
              user_data: OAuth2PasswordRequestForm = Depends()) -> JSONResponse:
        """
        Authenticate a user and generates an authorization token if successful.
        :param db: database session
        :param user_data: OAuth2 login credentials
        :return dict: access token, token type and username if successful
        """

        exc = HTTPException(status_code=400, detail="Incorrect username or password")
        user = UVal.find_user_with_or_raise_exception("username", user_data.username, db, exc)

        if not user:
            raise exc

        # TODO: Hash password
        if not user.hashed_password == user_data.password:
            raise exc

        if user.status == UStatus.BLOCKED:
            raise HTTPException(status_code=403, detail="Your account is blocked. Please contact support.")

        if user.status == UStatus.DEACTIVATED:
            user.status = UStatus.REACTIVATION
            db.commit()
            db.refresh(user)

            raise HTTPException(status_code=400, detail="Your account is deactivated. Log in again to reactivate.")

        if user.status == UStatus.REACTIVATION:
            user.status = UStatus.ACTIVE
            db.commit()
            db.refresh(user)

        # Create response and set cookie
        token = generate_token(user.username)
        response = JSONResponse(
            content={
                "access_token": token,
                "token_type": "Bearer",
                "username": user.username
            }
        )

        response.delete_cookie("access_token")
        response.set_cookie(key="access_token", value=token, httponly=False, secure=False, samesite="lax")
        return response

    @classmethod
    def set_status(cls, db: Session, user: User, status: UStatus = UStatus.ACTIVE) -> User:
        """
        Sets the status of a user.
        :param db: database session
        :param user: User object
        :param status: new user status
        :return: updated User object
        """
        db.refresh(user)
        user.status = status
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def get_status(cls, db: Session, user: User | str) -> UStatus:
        """
        Gets the status of a user.
        :param db: database session
        :param user: User object or username
        :return: the user's status
        """
        if isinstance(user, str):
            user = UVal.find_user_with_or_raise_exception("username", user, db)

        return user.status

    @classmethod
    def verify_user_can_deposit(cls, user: User) -> bool:
        """
        Checks if a user can deposit money.
        :param user: User object
        :return: True if user can deposit, raises exception otherwise
        """
        if user.status == UStatus.ACTIVE or user.admin:
            return True
        else:
            if len(user.deactivated_cards) <= 2 and user.completed_deposits_count <= 3:
                return True

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have reached your deposit limit for a pending account, please await approval"
        )

    @classmethod
    def verify_user_can_add_card(cls, user: User) -> bool:
        """
        Checks if a user can add cards.
        :param user: User object
        :return: True if user can add cards, raises exception otherwise
        """
        if user.status == UStatus.ACTIVE or user.admin:
            return True
        else:
            if len(user.deactivated_cards) <= 2 and len(user.active_cards) <= 3:
                return True

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have reached your cards limit for a pending account, please await approval"
        )

    @classmethod
    def update_user(cls, db: Session, user: User, update_data: UserUpdate):
        """Update user information"""
        data = update_data.model_dump()
        data = data_validators.validate_user_data(data)

        for key, value in data.items():
            if value is not None:
                user.__setattr__(key, value)

        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def verify_user_can_transact(cls, user: User):
        """
        helepr function for recurring transactions
        """
        if user.status == UStatus.ACTIVE or user.admin:
            return True
        else:
            return False

    @classmethod
    def change_user_password(cls, db, user, password, current_password):
        if not auth.check_hashed_password(current_password, user.hashed_password):
            raise HTTPException(status_code=403, detail="Invalid credentials")

        password = DataValidators.validate_password(password)
        user.hashed_password = auth.hash_password(password)
        db.commit()
        db.refresh(user)
        return user