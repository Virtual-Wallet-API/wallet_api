from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Float, String, Text
from sqlalchemy.orm import relationship, validates
from datetime import datetime
from app.infrestructure import Base
from fastapi import HTTPException


class Deposit(Base):
    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)

    # Amount and financial details
    amount = Column(Float, nullable=False)  # Amount in dollars
    amount_cents = Column(Integer, nullable=False)  # Amount in cents for precision

    # Deposit method and type
    deposit_type = Column(Enum("card_payment", "bank_transfer", "cash", "other", name="deposit_type"), nullable=False,
                          default="card_payment")
    method = Column(Enum("stripe", "manual", "bank", name="deposit_method"), nullable=False, default="stripe")

    # Status tracking
    status = Column(Enum("pending", "processing", "completed", "failed", "cancelled", name="deposit_status"),
                    nullable=False, default="pending")

    # Stripe integration fields
    stripe_payment_intent_id = Column(String(255), nullable=True, unique=True)  # Stripe payment intent ID
    stripe_charge_id = Column(String(255), nullable=True)  # Stripe charge ID
    stripe_customer_id = Column(String(255), nullable=True)  # Stripe customer ID

    # Metadata and tracking
    description = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    # Legacy field for backward compatibility
    date = Column(DateTime, default=datetime.utcnow, nullable=False)  # Keep for existing code
    type = Column(Enum("credit", "debit", name="card_type"), nullable=False, default="credit")  # Keep for existing code

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
        return self.status == "completed"

    @property
    def is_pending(self) -> bool:
        """Check if deposit is pending"""
        return self.status in ["pending", "processing"]

    @property
    def can_be_cancelled(self) -> bool:
        """Check if deposit can be cancelled"""
        return self.status in ["pending"]

    def mark_completed(self):
        """Mark deposit as completed"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()

    def mark_failed(self, reason: str = None):
        """Mark deposit as failed"""
        self.status = "failed"
        self.failed_at = datetime.utcnow()
        if reason:
            self.failure_reason = reason

    def mark_processing(self):
        """Mark deposit as processing"""
        self.status = "processing"



