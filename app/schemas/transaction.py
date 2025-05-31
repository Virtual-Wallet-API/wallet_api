from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.transaction import TransactionStatus, TransactionUpdateStatus
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
    status: TransactionUpdateStatus


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

    class Config:
        from_attributes = True
