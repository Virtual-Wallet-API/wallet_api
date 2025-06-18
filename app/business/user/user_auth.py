from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import JSONResponse
import jwt, datetime

from app.business.utils import NotificationService
from app.business.user.user_validators import UserValidators as UVal
from app.business.utils.notification_service import EmailTemplates
from app.dependencies import get_db
from app.infrestructure import generate_token, data_validators, auth, DataValidators, hash_email, hash_password, \
    check_hashed_password
from app.models import User, UStatus
from app.models.user import UserStatus
from app.schemas.user import UserCreate, UserUpdate
from app.config import SECRET_KEY, ALGORITHM


class UserAuthService:
    """Business logic for user authentication and authorization"""

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
                    hashed_password=hash_password(user_data.password),
                    email=user_data.email,
                    phone_number=user_data.phone_number,
                    email_key=hash_email(user_data.email).replace("/", "").replace(".", ""))

        db.add(user)
        db.commit()
        db.refresh(user)

        print(NotificationService.notify_from_template(EmailTemplates.EMAIL_VERIFICATION, user,
                                                       verification_link=user_data.email_verification_link, key=user.email_key))

        return user

    @classmethod
    def verifty_email(cls,
                      db: Session,
                      key: str = None):
        """Verify a user email using unique email key"""

        exc = HTTPException(status_code=400, detail="Invalid activation link")
        if not key:
            raise exc

        key_check = db.query(User).filter(User.email_key == key).first()

        if not key_check or key_check.email_key != key:
            raise exc

        if key_check.status != UStatus.EMAIL:
            raise exc

        key_check.status = UStatus.PENDING
        key_check.email_key = None
        db.commit()

        return {"detail": "Email successfully verified"}

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

        if not check_hashed_password(user_data.password, user.hashed_password):
            raise exc

        if user.status == UserStatus.EMAIL:
            raise HTTPException(status_code=412, detail="Your email address is not verified, please check your inbox")

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

    @classmethod
    def request_password_reset(cls, db, email):
        """
        Generate a password reset token and send a reset link to the user's email.
        - If the email exists, sends a reset link with a secure, time-limited token.
        - Always returns a generic message for security.
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"detail": "If the email exists, a reset link has been sent."}
        payload = {
            "sub": user.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            "purpose": "password_reset"
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        reset_link = f"http://vwallet.ninja/reset-password?token={token}"
        NotificationService.notify_from_template(EmailTemplates.PASSWORD_RESET, user, reset_link=reset_link)
        return {"detail": "If the email exists, a reset link has been sent."}

    @classmethod
    def reset_password(cls, db, token, new_password):
        """
        Reset the user's password using the provided token.
        - Verifies the token and sets the new password.
        - Raises HTTP 400 if the token is invalid or expired.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("purpose") != "password_reset":
                raise jwt.InvalidTokenError()
            username = payload["sub"]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        # Validate the new password
        validated_password = DataValidators.validate_password(new_password)
        
        # Hash the password before storing
        user.hashed_password = auth.hash_password(validated_password)
        db.commit()
        
        return {"detail": "Password has been reset successfully."}
