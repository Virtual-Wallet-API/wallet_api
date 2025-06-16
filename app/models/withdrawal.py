from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import HTTPException
from pydantic_core import core_schema
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String, Text
from sqlalchemy.orm import relationship, validates
from sqlalchemy.types import Enum as CEnum

from app.infrestructure import Base
from app.schemas import CardPublicResponse, UserPublicResponse


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


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)  # Nullable for bank transfers
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)

    # Amount and financial details
    amount = Column(Float, nullable=False)  # Amount in dollars
    amount_cents = Column(Integer, nullable=False)  # Amount in cents for precision

    # Withdrawal method and type
    withdrawal_type = Column(CEnum(WithdrawalType, name="withdrawal_type",
                                   values_callable=lambda obj: [e.value for e in obj]),
                             nullable=False)

    method = Column(CEnum(WithdrawalMethod, name="withdrawal_method",
                          values_callable=lambda obj: [e.value for e in obj]),
                    nullable=False,
                    default=WithdrawalMethod.CARD)

    # Status tracking
    status = Column(CEnum(WithdrawalStatus, name="withdrawal_status",
                          values_callable=lambda obj: [e.value for e in obj]),
                    nullable=False,
                    default=WithdrawalStatus.PENDING)

    # Stripe integration fields
    stripe_payout_id = Column(String(255), nullable=True)  # Stripe payout ID
    stripe_refund_id = Column(String(255), nullable=True)  # Stripe refund ID
    stripe_payment_intent_id = Column(String(255), nullable=True)  # Original payment intent for refunds

    # Metadata and tracking
    description = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    estimated_arrival = Column(String(100), nullable=True)  # e.g., "1-3 business days"

    # Timestamps
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="withdrawals")
    card = relationship("Card", back_populates="withdrawals")
    currency = relationship("Currency", back_populates="withdrawals")

    # Pydantic type error fix

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:
        return handler(core_schema.model_schema(cls))

    # Validators

    @validates("amount")
    def validate_amount(self, key, v: float) -> float:
        if v <= 0:
            raise HTTPException(status_code=400,
                                detail="Amount must be positive")
        return v

    @validates("amount_cents")
    def validate_amount_cents(self, key, v: int) -> int:
        if v <= 0:
            raise HTTPException(status_code=400,
                                detail="Amount in cents must be positive")
        return v

    # Properties

    @property
    def card_last_four(self):
        return self.card.last_four

    @property
    def is_completed(self) -> bool:
        """Check if withdrawal is completed"""
        return self.status == WithdrawalStatus.COMPLETED

    @property
    def is_pending(self) -> bool:
        """Check if withdrawal is pending"""
        return self.status in [WithdrawalStatus.PENDING, WithdrawalStatus.PROCESSING]

    @property
    def can_be_cancelled(self) -> bool:
        """Check if withdrawal can be cancelled"""
        return self.status in [WithdrawalStatus.PENDING]

    @property
    def card_info(self) -> CardPublicResponse | None:
        return CardPublicResponse.model_validate(self.card) if self.card else None

    @property
    def user_info(self) -> UserPublicResponse:
        return UserPublicResponse.model_validate(self.user)

    def mark_completed(self):
        """Mark withdrawal as completed"""
        self.status = WithdrawalStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_failed(self, reason: str = None):
        """Mark withdrawal as failed"""
        self.status = WithdrawalStatus.FAILED
        self.failed_at = datetime.now()
        if reason:
            self.failure_reason = reason

    def mark_processing(self):
        """Mark withdrawal as processing"""
        self.status = WithdrawalStatus.PROCESSING

    def __repr__(self) -> str:
        return f"<Withdrawal #{self.id} | ${self.amount} | {self.status} | User {self.user_id}>"
