from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, field_validator


# Schema for refund response
class RefundResponse(BaseModel):
    refund_id: str
    amount: int  # Amount in cents
    currency: str
    status: str
    reason: Optional[str]
    created_at: datetime
    withdrawal_id: Optional[int] = None  # Link to our tracking record


class WithdrawalType(str, Enum):
    REFUND = "refund"
    PAYOUT = "payout"
    BANK_TRANSFER = "bank_transfer"


class WithdrawalMethod(str, Enum):
    CARD = "card"
    BANK_ACCOUNT = "bank_account"
    INSTANT = "instant"
    STANDARD = "standard"


class WithdrawalStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Base withdrawal schema
class WithdrawalBase(BaseModel):
    amount: float
    amount_cents: int
    description: Optional[str] = None


# Schema for creating a withdrawal
class WithdrawalCreate(BaseModel):
    amount_cents: int  # Amount in cents for precision
    card_id: Optional[int] = None
    currency_code: str = "USD"
    withdrawal_type: WithdrawalType = WithdrawalType.PAYOUT
    method: WithdrawalMethod = WithdrawalMethod.CARD
    description: Optional[str] = None

    @field_validator('amount_cents')
    @classmethod
    def validate_amount_cents(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v > 100000000:  # $1M limit
            raise ValueError('Amount exceeds maximum limit')
        return v


# Schema for refund creation
class RefundCreate(BaseModel):
    amount_cents: int
    stripe_payment_intent_id: str
    reason: Optional[str] = "requested_by_customer"
    description: Optional[str] = None

    @field_validator('amount_cents')
    @classmethod
    def validate_amount_cents(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


# Schema for withdrawal update
class WithdrawalUpdate(BaseModel):
    status: Optional[WithdrawalStatus] = None
    failure_reason: Optional[str] = None
    stripe_payout_id: Optional[str] = None
    stripe_refund_id: Optional[str] = None
    estimated_arrival: Optional[str] = None


# Schema for withdrawal response
class WithdrawalResponse(BaseModel):
    id: int
    user_id: int
    card_id: Optional[int]
    amount: float
    amount_cents: int
    withdrawal_type: WithdrawalType
    method: WithdrawalMethod
    status: WithdrawalStatus
    description: Optional[str]
    failure_reason: Optional[str]
    estimated_arrival: Optional[str]
    stripe_payout_id: Optional[str]
    stripe_refund_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Schema for public withdrawal response (limited info)
class WithdrawalPublicResponse(BaseModel):
    id: int
    amount: float
    withdrawal_type: WithdrawalType
    method: WithdrawalMethod
    status: WithdrawalStatus
    description: Optional[str]
    estimated_arrival: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    card_info: Optional[dict] = None  # Card details if applicable

    class Config:
        from_attributes = True


# Schema for withdrawal history
class WithdrawalHistoryResponse(BaseModel):
    withdrawals: List[WithdrawalPublicResponse]
    total: int
    total_amount: float
    pending_amount: float


# Schema for withdrawal statistics
class WithdrawalStatsResponse(BaseModel):
    total_withdrawals: int
    total_amount: float
    completed_withdrawals: int
    pending_withdrawals: int
    failed_withdrawals: int
    average_amount: float
    total_refunds: int
    total_payouts: int
    refund_amount: float
    payout_amount: float