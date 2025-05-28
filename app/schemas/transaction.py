from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.transaction import TransactionStatus
from app.schemas.user import ShortUserResponse


class TransactionBase(BaseModel):
    sender_id: int
    receiver_id: int
    amount: float
    description: Optional[str] = None
    category_id: Optional[int] = None
    currency_id: int


class TransactionCreate(BaseModel):
    receiver_id: int
    amount: float
    description: Optional[str] = None
    category_id: Optional[int] = None
    currency_id: int


class TransactionResponse(TransactionBase):
    id: int
    date: datetime
    status: TransactionStatus

    class Config:
        from_attributes = True


class CategoryTransactionResponse(BaseModel):
    date: datetime
    sender: ShortUserResponse
    receiver: ShortUserResponse
    amount: float
    description: Optional[str] = None
    status: TransactionStatus

    class Config:
        from_attributes = True


class TransactionHistoryResponse(BaseModel):
    transactions: List[TransactionResponse] = []
    total: int = 0
    outgoing_total: float = 0.0
    incoming_total: float = 0.0

    class Config:
        from_attributes = True
