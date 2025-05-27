from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, field_validator


class DepositType(str, Enum):
    CARD_PAYMENT = "card_payment"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    OTHER = "other"


class DepositMethod(str, Enum):
    STRIPE = "stripe"
    MANUAL = "manual"
    BANK = "bank"


class DepositStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Base deposit schema
class DepositBase(BaseModel):
    amount: float
    amount_cents: int
    description: Optional[str] = None


# Schema for creating a deposit
class DepositCreate(BaseModel):
    amount_cents: int  # Amount in cents for precision
    card_id: Optional[int] = None
    currency_code: str = "USD"
    deposit_type: DepositType = DepositType.CARD_PAYMENT
    method: DepositMethod = DepositMethod.STRIPE
    description: Optional[str] = None
    save_payment_method: bool = False  # Whether to save card for future use

    @field_validator('amount_cents')
    @classmethod
    def validate_amount_cents(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v < 50:  # Minimum $0.50
            raise ValueError('Amount must be at least $0.50')
        if v > 100000000:  # $1M limit
            raise ValueError('Amount exceeds maximum limit')
        return v


# Schema for deposit via existing card
class DepositWithCard(BaseModel):
    amount_cents: int
    card_id: int
    description: Optional[str] = None
    currency_code: str = "USD"

    @field_validator('amount_cents')
    @classmethod
    def validate_amount_cents(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v < 50:  # Minimum $0.50
            raise ValueError('Amount must be at least $0.50')
        return v


# Schema for deposit update
class DepositUpdate(BaseModel):
    status: Optional[DepositStatus] = None
    failure_reason: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    completed_at: Optional[datetime] = None


# Schema for deposit response
class DepositResponse(BaseModel):
    id: int
    user_id: int
    card_id: Optional[int]
    amount: float
    amount_cents: int
    deposit_type: DepositType
    method: DepositMethod
    status: DepositStatus
    description: Optional[str]
    failure_reason: Optional[str]
    stripe_payment_intent_id: Optional[str]
    stripe_charge_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Schema for public deposit response (limited info)
class DepositPublicResponse(BaseModel):
    id: int
    amount: float
    deposit_type: DepositType
    method: DepositMethod
    status: DepositStatus
    description: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    card_last_four: Optional[str] = None

    class Config:
        from_attributes = True


# Schema for deposit history
class DepositHistoryResponse(BaseModel):
    deposits: List[DepositPublicResponse]
    total: int
    total_amount: float
    pending_amount: float


# Schema for deposit statistics
class DepositStatsResponse(BaseModel):
    total_deposits: int
    total_amount: float
    completed_deposits: int
    pending_deposits: int
    failed_deposits: int
    average_amount: float


# Schema for payment intent creation (for new cards)
class DepositPaymentIntentCreate(BaseModel):
    amount_cents: int
    currency: str = "usd"
    description: Optional[str] = "Wallet deposit"
    save_payment_method: bool = False
    payment_method_id: str

    @field_validator('amount_cents')
    @classmethod
    def validate_amount_cents(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v < 50:  # Minimum $0.50
            raise ValueError('Amount must be at least $0.50')
        return v


# Schema for payment intent response
class DepositPaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str
    status: str
    deposit_id: int  # Our internal deposit record ID


# Schema for confirming a deposit
class DepositConfirm(BaseModel):
    payment_intent_id: str
    save_card: bool = False
    cardholder_name: Optional[str] = None
