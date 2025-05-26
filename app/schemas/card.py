from datetime import datetime
from enum import Enum
from typing import Optional, List, ForwardRef

from pydantic import BaseModel, field_validator

UserResponse = ForwardRef("UserResponse")


class CardType(Enum):
    DEBIT = "debit"
    CREDIT = "credit"
    UNKNOWN = "unknown"


class CardBrand(Enum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    DINERS = "diners"
    JCB = "jcb"
    UNIONPAY = "unionpay"
    UNKNOWN = "unknown"


# Base schema for card information (safe fields only)
class CardBase(BaseModel):
    cardholder_name: str
    design: Optional[str] = '{"color": "purple"}'


# Schema for adding a new card via Stripe
class CardCreate(CardBase):
    # This will be used when creating a card through Stripe Elements
    # The actual card details will be handled by Stripe on the frontend
    pass


# Schema for card setup intent (for saving cards without charging)
class CardSetupRequest(BaseModel):
    save_for_future: bool = True


# Schema for payment intent creation
class PaymentIntentCreate(BaseModel):
    amount: int  # Amount in cents
    currency: str = "usd"
    description: Optional[str] = None
    save_payment_method: bool = False


# Response schema for payment intent
class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str
    status: str


# Response schema for setup intent
class SetupIntentResponse(BaseModel):
    client_secret: str
    setup_intent_id: str
    status: str


# Withdrawal schemas
class WithdrawalRequest(BaseModel):
    amount: int  # Amount in cents
    card_id: int
    description: Optional[str] = "Wallet withdrawal"
    currency: str = "usd"


class RefundRequest(BaseModel):
    amount: int  # Amount in cents
    payment_intent_id: str
    reason: Optional[str] = "requested_by_customer"
    description: Optional[str] = "Refund to original payment method"


class WithdrawalResponse(BaseModel):
    withdrawal_id: str
    amount: int
    currency: str
    status: str
    card_last_four: str
    created_at: datetime
    estimated_arrival: Optional[str] = None


class RefundResponse(BaseModel):
    refund_id: str
    amount: int
    currency: str
    status: str
    reason: str
    created_at: datetime


# Schema for card response (safe information only)
class CardResponse(BaseModel):
    id: int
    last_four: str
    brand: str
    exp_month: int
    exp_year: int
    cardholder_name: str
    type: CardType
    design: str
    is_default: bool
    is_active: bool
    created_at: datetime

    @property
    def masked_number(self) -> str:
        return f"**** **** **** {self.last_four}"

    @property
    def is_expired(self) -> bool:
        now = datetime.now()
        return (self.exp_year < now.year) or (self.exp_year == now.year and self.exp_month < now.month)

    class Config:
        from_attributes = True


# Public card response (for API responses)
class CardPublicResponse(BaseModel):
    id: int
    last_four: str
    brand: str
    exp_month: int
    exp_year: int
    cardholder_name: str
    type: CardType
    design: str
    is_default: bool
    is_active: bool
    masked_number: str
    is_expired: bool

    class Config:
        from_attributes = True


# Schema for updating card information
class CardUpdate(BaseModel):
    cardholder_name: Optional[str] = None
    design: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


# Schema for card deletion/deactivation
class CardDelete(BaseModel):
    confirm: bool = True


# List of cards response
class CardListResponse(BaseModel):
    cards: List[CardPublicResponse]
    total: int
    has_default: bool


CardPublicResponse.model_rebuild()