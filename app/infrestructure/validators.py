from fastapi import HTTPException


def validate_username(v: str) -> str:
    """
        Check if a username is between 2 and 20 characters long
    """
    if len(v) < 2 or len(v) > 20:
        raise HTTPException(status_code=400, detail="Username must be between 2 and 20 characters long")

    return v


def validate_password(v: str):
    """
        Check if a password is at least 8 characters long
    """
    if len(v) < 8:
        raise HTTPException(status_code=400,
                            detail="Password must be at least 8 characters long")

    if not any(char.isdigit() for char in v) \
            or not any(char.isupper() for char in v) \
            or all(char.isalnum() for char in v):
        raise HTTPException(status_code=400,
                            detail="Password must contain at least one digit, one uppercase letter and one special character")
    return v


def validate_phone_number(v: str):
    """
        Validate a phone number
    """
    if len(v) != 10:
        raise HTTPException(status_code=400, detail="Phone number must be valid")
    return v
