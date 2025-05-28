from typing import Optional, List

from pydantic import BaseModel

from app.models import UStatus
from app.schemas import UserResponse
from app.schemas.transaction import TransactionResponse


class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    phone_number: str
    balance: float = 0.0
    contacts_count: int = 0
    cards_count: int = 0
    transactions_count: int = 0
    deposits_count: int = 0
    withdrawals_count: int = 0
    status: UStatus
    avatar: Optional[str] = None

    class Config:
        from_attributes = True

class ListAllUsersResponse(BaseModel):
    users: List[AdminUserResponse] = []
    page: int = 1
    matching_records: int = 0
    pages_with_matches: int = 0
    results_per_page: int = 30

    class Config:
        from_attributes = True


class UpdateUserStatus(BaseModel):
    user: int
    status: UStatus
    reason: Optional[str] = None


class UpdateUserStatusResponse(BaseModel):
    user: UserResponse
    message: str

    class Config:
        from_attributes = True


class ListAllUserTransactionsResponse(BaseModel):
    transactions: List[TransactionResponse] = []
    page: int = 1
    matching_records: int = 0
    pages_with_matches: int = 1
    results_per_page: int = 30