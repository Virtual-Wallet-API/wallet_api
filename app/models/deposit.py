from datetime import datetime
from enum import Enum

from fastapi import HTTPException
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String, Text
from sqlalchemy.types import Enum as CEnum
from sqlalchemy.orm import relationship, validates

from app.infrestructure import Base


class DepositStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DepositMethod(Enum):
    STRIPE = "stripe"
    MANUAL = "manual"
    BANK = "bank"


class DepositType(Enum):
    CARD_PAYMENT = "card_payment"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    OTHER = "other"


class Deposit(Base):
    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)

    # Amount and financial details
    amount = Column(Float, nullable=False)  # Amount in dollars
    amount_cents = Column(Integer, nullable=False)  # Amount in cents for precision

    # Deposit method and type
    method = Column(CEnum(DepositMethod, name="deposit_method", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=DepositMethod.STRIPE)
    deposit_type = Column(CEnum(DepositType,name="deposit_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=DepositType.CARD_PAYMENT)

    # Status tracking
    status = Column(CEnum(DepositStatus, name="deposit_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default="pending")

    # Stripe integration fields
    stripe_payment_intent_id = Column(String(255), nullable=True, unique=True)  # Stripe payment intent ID
    stripe_payment_intent_secret = Column(String(255), nullable=True)
    stripe_charge_id = Column(String(255), nullable=True)  # Stripe charge ID
    stripe_customer_id = Column(String(255), nullable=True)  # Stripe customer ID

    # Metadata and tracking
    description = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="deposits")
    currency = relationship("Currency", back_populates="deposits")
    card = relationship("Card", back_populates="deposits")

    @validates("amount")
    def validate_amount(self, key, v: float):
        if v <= 0:
            raise HTTPException(status_code=400,
                                detail="Amount must be positive")
        return v

    @validates("amount_cents")
    def validate_amount_cents(self, key, v: int):
        if v <= 0:
            raise HTTPException(status_code=400,
                                detail="Amount in cents must be positive")
        return v

    def __repr__(self):
        return f"<Deposit #{self.id} | ${self.amount} | {self.status} | User {self.user_id}>"

    @property
    def is_completed(self) -> bool:
        """Check if deposit is completed"""
        return self.status == DepositStatus.COMPLETED

    @property
    def is_pending(self) -> bool:
        """Check if deposit is pending"""
        return self.status in (DepositStatus.PENDING, DepositStatus.PROCESSING)

    @property
    def is_cancelled_or_failed(self) -> bool:
        """Check if deposit is cancelled or has failed"""
        return self.status in (DepositStatus.CANCELLED, DepositStatus.FAILED)

    @property
    def can_be_cancelled(self) -> bool:
        """Check if deposit can be cancelled"""
        return self.status in (DepositStatus.PENDING,)

    def mark_completed(self):
        """Mark deposit as completed"""
        self.status = DepositStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_failed(self, reason: str = None):
        """Mark deposit as failed"""
        self.status = DepositStatus.FAILED
        self.failed_at = datetime.now()
        if reason:
            self.failure_reason = reason

    def mark_processing(self):
        """Mark deposit as processing"""
        self.status = DepositStatus.PROCESSING
