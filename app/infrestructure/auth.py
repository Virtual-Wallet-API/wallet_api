from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from starlette import status

from app.config import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES

hash_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

exception_headers = {"WWW-Authenticate": "Bearer"}

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers=exception_headers,
)

invalid_credentials = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers=exception_headers,
)

expired_token = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication token expired",
    headers=exception_headers,
)

forbidden_access = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Access denied"
)

email_verification_user = HTTPException(
    status_code=status.HTTP_412_PRECONDITION_FAILED,
    detail="Unconfirmed email, please check your email and follow the instructions to verify your email"
)

unknown_verification_key = HTTPException

pending_user = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User is pending, awaiting approval"
)

deactivated_user = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User is deactivated, reactivate to access"
)

blocked_user = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User is blocked"
)

forced_password_reset = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User is required to reset password before access to this resource",
    headers={"X-Force-Password-Reset": "true"}
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
        Hashes a password using bcrypt.
    """
    return pwd_context.hash(password)


def hash_email(email: str) -> str:
    """
        Hashes a password using bcrypt.
    """
    return pwd_context.hash(email)


def check_hashed_password(plain_password: str, hashed_password: str) -> bool:
    """
        Checks if a plain password matches a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)


def verify_token(token: str):
    """
        Verifies the validity of an authentication token.
    """
    try:
        if isinstance(token, str):
            token = token.encode('utf-8')

        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)

        exp = payload.get("exp")
        username: str = payload.get("sub")
        if not exp or not username:
            raise credentials_exception

        try:
            if exp < datetime.now().timestamp():
                raise expired_token
        except TypeError:
            raise invalid_credentials

        return username
    except jwt.PyJWTError as e:
        print(f"Error decoding token: {e}")
        raise credentials_exception


def generate_token(username: str):
    """
        Generates an authentication token.
    """
    expire = (datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
    to_encode = {"exp": expire, "sub": username}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
