from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException

from passlib.context import CryptContext
from starlette import status

from app.config import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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


def verify_token(token: str):
    """
        Verifies the validity of an authentication token.
    """
    try:
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
