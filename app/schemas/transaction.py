from datetime import datetime
from enum import Enum
from typing import Optional, List, Literal

from pydantic import BaseModel, field_validator

from app.models.transaction import TransactionStatus, TransactionUpdateStatus
from app.schemas.user import ShortUserResponse


class TransactionBase(BaseModel):
    sender_id: int
    receiver_id: int
    amount: float
    description: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    currency_id: int


class TransactionCreateIdentifiers(str, Enum):
    USERNAME = "username"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"


class TransactionCreate(BaseModel):
    identifier: str
    amount: float
    description: Optional[str] = None
    category_id: Optional[int] = None
    currency_id: int = 1
    recurring: bool = False
    interval: Optional[Literal["day", "week", "month"]] = None

    @field_validator('category_id')
    def category_id_must_be_positive(cls, v):
        if isinstance(v, int) and v < 1:
            return None
        return v

    @field_validator("currency_id")
    def currency_id_null(cls, v):
        if isinstance(v, int) and v == 0:
            return 1
        return v


class TransactionConfirm(BaseModel):
    """Schema for confirming a transaction"""
    pass  # No additional data needed for confirmation


class TransactionAccept(BaseModel):
    """Schema for receiver accepting a pending transaction"""
    message: Optional[str] = None  # Optional message from receiver


class TransactionDecline(BaseModel):
    """Schema for receiver declining a pending transaction"""
    reason: Optional[str] = None  # Optional reason for declining


class TransactionStatusUpdate(BaseModel):
    action: TransactionUpdateStatus


class TransactionResponse(TransactionBase):
    id: int
    date: datetime
    status: TransactionStatus

    class Config:
        from_attributes = True


class TransactionDetailResponse(TransactionResponse):
    """Extended transaction response with sender/receiver info"""
    sender: ShortUserResponse
    receiver: ShortUserResponse

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
    avg_outgoing_transaction: float = 0.0
    avg_incoming_transaction: float = 0.0
    net_total: float = 0.0

    class Config:
        from_attributes = True