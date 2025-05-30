from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models import UStatus
from app.models.transaction import TransactionStatus
from app.schemas import UserResponse


class ShortAdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    phone_number: str

    class Config:
        from_attributes = True


class AdminUserResponse(ShortAdminUserResponse):
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
    status: UStatus
    reason: Optional[str] = None


class UpdateUserStatusResponse(BaseModel):
    user: UserResponse
    message: str

    class Config:
        from_attributes = True


class AdminTransactionResponse(BaseModel):
    id: int
    sender: ShortAdminUserResponse
    receiver: ShortAdminUserResponse
    amount: float
    currency_id: int
    status: TransactionStatus
    date: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ListAllUserTransactionsResponse(BaseModel):
    transactions: Optional[List[AdminTransactionResponse]] = []
    page: int = 1
    matching_records: int = 0
    pages_with_matches: int = 1
    results_per_page: int = 30

    class Config:
        from_attributes = True
