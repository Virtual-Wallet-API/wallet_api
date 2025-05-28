from enum import Enum
from typing import Optional, List, ForwardRef

from pydantic import BaseModel, EmailStr, field_validator

from app.infrestructure import data_validators
from app.schemas.contact import ContactResponse

ContactPublicResponse = ForwardRef("ContactPublicResponse")
CardPublicResponse = ForwardRef("CardPublicResponse")


class Status(str, Enum):
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

    @field_validator('password')
    def validate_password(cls, v: str) -> str:
        return data_validators.validate_password(v)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    balance: Optional[float] = None
    avatar: Optional[str] = None
    status: Optional[Status] = None
    admin: Optional[bool] = None

    @field_validator('username')
    def validate_username(cls, v: str) -> str:
        return data_validators.validate_username(v)

    @field_validator('password')
    def validate_password(cls, v: str) -> str:
        return data_validators.validate_password(v)

    @field_validator('email')
    def validate_email(cls, v: str) -> str:
        return data_validators.validate_email(v)


class UserPublicResponse(UserPublicBase):
    id: int
    status: Status = Status.pending

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    balance: float = 0.0
    contacts: List["ContactResponse"] = []
    cards: List["CardPublicResponse"] = []
    status: Status = Status.pending
    admin: bool = False

    class Config:
        from_attributes = True
