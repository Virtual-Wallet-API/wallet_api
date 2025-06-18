from fastapi import HTTPException


class DataValidators:
    _UserValidators: dict  # Mapping user validators

    def __init__(self):
        self._UserValidators = {
            "username": self.validate_username,
            "password": self.validate_password,
            "phone_number": self.validate_phone_number,
            "email": self.validate_email,
        }

    @property
    def UserValidators(self):
        return self._UserValidators

    def validate_user_data(self, data: dict) -> dict:
        """
            Validate user data input - username, email, and phone number
        """
        returnData = {}

        for field, value in data.items():
            if value and field in self._UserValidators:
                returnData[field] = self._UserValidators[field](value)
            else:
                returnData[field] = value

        return returnData

    @classmethod
    def validate_username(cls, v: str) -> str:
        """
            Check if a username is between 3 and 20 alphanumeric characters
        """
        if not (3 <= len(v) <= 20) or not v.isalnum():
            raise HTTPException(status_code=400, detail="Username must be 3-20 alphanumeric characters")
        return v

    @classmethod
    def validate_password(cls, v: str) -> str:
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

    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """
            Validate a phone number
        """
        if len(v) != 10:
            raise HTTPException(status_code=400, detail="Phone number must be valid")
        return v

    @classmethod
    def validate_email(cls, v: str) -> str:
        """
            Validate an email address
        """
        if v.count("@") != 1 or "." not in v or v.endswith("@") or v.startswith("@") \
                or v.startswith(".") or v.endswith(".") or (v.count("@.") + v.count(".@")) != 0 \
                or v.split("@")[1].count(".") == 0:
            raise HTTPException(status_code=400, detail="Email address must be valid")
        return v
