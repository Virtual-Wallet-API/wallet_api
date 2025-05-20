from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    nickname: Optional[str] = None


class UserCreate(UserBase):
    hashed_password: str
    email: str
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime
    last_login: datetime

class UserUpdate(UserBase):
    nickname: Optional[str] = None