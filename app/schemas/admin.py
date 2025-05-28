from typing import Optional

from pydantic import BaseModel

from app.models import UStatus
from app.schemas import UserResponse


class UpdateUserStatus(BaseModel):
    user: int
    status: UStatus
    reason: Optional[str] = None


class UpdateUserStatusResponse(BaseModel):
    user: UserResponse
    message: str

    class Config:
        from_attributes = True
