from enum import Enum
from datetime import datetime
from typing import Optional, ForwardRef
from pydantic import BaseModel


class TransactionStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class TransactionBase(BaseModel):
    sender_id: int
    receiver_id: int
    amount: float
    category_id: int
    currency_id: int

class TransactionCreate(TransactionBase):
    date: datetime


class TransactionResponse(TransactionBase):
    id: int
    date: datetime
    status: TransactionStatus

    class Config:
        from_attributes = True