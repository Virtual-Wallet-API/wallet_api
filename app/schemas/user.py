from enum import Enum
from typing import Optional, ForwardRef

from pydantic import BaseModel, EmailStr, field_validator

from app.infrestructure import data_validators

ContactPublicResponse = ForwardRef("ContactPublicResponse")
CardPublicResponse = ForwardRef("CardPublicResponse")


class Status(str, Enum):
    email = "email_verification"
    blocked = "blocked"
    deactivated = "deactivated"
    pending = "pending"
    active = "active"


class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    avatar: Optional[str] = None

    @field_validator('username')
    def validate_username(cls, v: str) -> str:
        return data_validators.validate_username(v)

    @field_validator('email')
    def validate_email(cls, v: str) -> str:
        return data_validators.validate_email(v)

    @field_validator('phone_number')
    def validate_phone_number(cls, v: str) -> str:
        return data_validators.validate_phone_number(v)


class UserPublicBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    avatar: Optional[str] = None

    @field_validator('username')
    def validate_username(cls, v: str) -> str:
        return data_validators.validate_username(v)

    @field_validator('email')
    def validate_email(cls, v: str) -> str:
        return data_validators.validate_email(v)

    @field_validator('phone_number')
    def validate_phone_number(cls, v: str) -> str:
        return data_validators.validate_phone_number(v)


class UserCreate(UserBase):
    password: str
    email_verification_link: Optional[str] = "http://127.0.0.1/verify/"

    @field_validator('password')
    def validate_password(cls, v: str) -> str:
        return data_validators.validate_password(v)

    class Config:
        exclude = {"avatar"}


class UserUpdate(BaseModel):
    phone_number: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None

    @field_validator('email')
    def validate_email(cls, v: str) -> str:
        return data_validators.validate_email(v)

    @field_validator('phone_number')
    def validate_phone_number(cls, v: str) -> str:
        return data_validators.validate_phone_number(v)


class UserPublicResponse(UserPublicBase):
    id: int
    status: Status = Status.pending

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    balance: float = 0.0
    reserved_balance: float = 0.0
    status: Status = Status.pending
    admin: bool = False

    class Config:
        from_attributes = True


class ShortUserResponse(BaseModel):
    username: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    """
    Request schema for initiating a password reset.
    - email: The user's email address.
    """
    email: str


class PasswordResetConfirm(BaseModel):
    """
    Request schema for confirming a password reset.
    - token: The password reset token sent to the user's email.
    - new_password: The new password to set.
    """
    token: str
    new_password: str

UserResponse.model_rebuild()