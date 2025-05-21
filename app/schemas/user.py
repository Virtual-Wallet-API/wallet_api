from typing import Optional
from pydantic import BaseModel, field_validator, EmailStr

from app.infrestructure import validate_username, validate_password, validate_phone_number


class UserBase(BaseModel):
    username: str
    avatar: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    hashed_password: str
    email: EmailStr
    phone_number: str

    @field_validator("username")
    def validate_username(cls, v: str) -> str:
        return validate_username(v)

    @field_validator("hashed_password")
    def validate_password(cls, v: str):
        return validate_password(v)

    @field_validator("phone_number")
    def validate_phone_number(cls, v: int):
        return validate_phone_number(v)

    class Config:
        from_attributes = True


class UserPublicResponse(UserBase):
    id: int
    admin: bool
    status: str


class UserPrivateResponse(UserBase):
    id: int
    email: EmailStr
    phone_number: str
    balance: float
    status: str
    admin: bool


class UserUpdate(UserBase):
    # Include updatable fields here
    pass
