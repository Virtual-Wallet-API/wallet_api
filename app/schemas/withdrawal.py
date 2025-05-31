from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, field_validator

from app.models.withdrawal import WithdrawalType, WithdrawalMethod, WithdrawalStatus
from app.schemas import CardPublicResponse, CardResponse


# Schema for refund response
class RefundResponse(BaseModel):
    refund_id: str
    amount: int  # Amount in cents
    currency: str
    status: str
    reason: Optional[str]
    created_at: datetime
    withdrawal_id: Optional[int] = None  # Link to our tracking record

    class Config:
        from_attributes = True


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
    card: CardPublicResponse
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

    model_config = {
        "from_attributes": True
    }


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
    card_info: Optional[CardPublicResponse] = None

    # @field_validator('withdrawal_type', mode='before')
    # @classmethod
    # def validate_withdrawal_type(cls, v):
    #     if isinstance(v, str):
    #         return WithdrawalType(v)
    #     return v
    #
    # @field_validator('method', mode='before')
    # @classmethod
    # def validate_method(cls, v):
    #     if isinstance(v, str):
    #         return WithdrawalMethod(v)
    #     return v
    #
    # @field_validator('status', mode='before')
    # @classmethod
    # def validate_status(cls, v):
    #     if isinstance(v, str):
    #         return WithdrawalStatus(v)
    #     return v

    # @model_serializer
    # def ser_model(self):
    #     return {
    #         "id": self.id,
    #         "amount": self.amount,
    #         "withdrawal_type": self.withdrawal_type,
    #         "method": self.method,
    #         "status": self.status,
    #         "description": self.description,
    #         "estimated_arrival": self.estimated_arrival,
    #         "created_at": self.created_at,
    #         "completed_at": self.completed_at,
    #         "card_info": self.card_info
    #     }

    model_config = {
        "from_attributes": True
    }


# Schema for withdrawal history
class WithdrawalHistoryResponse(BaseModel):
    withdrawals: List[WithdrawalPublicResponse]
    total: int = 0
    found_total: int = 0
    total_amount: float = 0.0
    found_amount: float = 0.0
    pending_amount: float = 0.0

    model_config = {
        "from_attributes": True,
    }


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

    class Config:
        from_attributes = True
