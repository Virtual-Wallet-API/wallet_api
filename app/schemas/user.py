from enum import Enum
from typing import Optional, List, ForwardRef
from pydantic import BaseModel, EmailStr

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
    balance: float = 0
    admin: bool = False
    avatar: Optional[str] = None
    status: Status = Status.pending


class UserPublicBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    avatar: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    balance: Optional[float] = None
    avatar: Optional[str] = None
    status: Optional[Status] = None
    admin: Optional[bool] = None


class UserPublicResponse(UserPublicBase):
    id: int
    status: Status = Status.pending


    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    contacts: List["ContactResponse"] = []
    cards: List["CardPublicResponse"] = []
    status: Status = Status.pending
    admin: bool = False

    class Config:
        from_attributes = True


