from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Float, String, Text
from sqlalchemy.orm import relationship, validates

from app.infrestructure import Base


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
    withdrawal_type = Column(Enum("refund", "payout", "bank_transfer", name="withdrawal_type"), nullable=False)
    method = Column(Enum("card", "bank_account", "instant", "standard", name="withdrawal_method"), nullable=False,
                    default="card")

    # Status tracking
    status = Column(Enum("pending", "processing", "completed", "failed", "cancelled", name="withdrawal_status"),
                    nullable=False, default="pending")

    # Stripe integration fields
    stripe_payout_id = Column(String(255), nullable=True)  # Stripe payout ID
    stripe_refund_id = Column(String(255), nullable=True)  # Stripe refund ID
    stripe_payment_intent_id = Column(String(255), nullable=True)  # Original payment intent for refunds

    # Metadata and tracking
    description = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    estimated_arrival = Column(String(100), nullable=True)  # e.g., "1-3 business days"

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="withdrawals")
    card = relationship("Card", back_populates="withdrawals")
    currency = relationship("Currency", back_populates="withdrawals")

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
        return f"<Withdrawal #{self.id} | ${self.amount} | {self.status} | User {self.user_id}>"

    @property
    def is_completed(self) -> bool:
        """Check if withdrawal is completed"""
        return self.status == "completed"

    @property
    def is_pending(self) -> bool:
        """Check if withdrawal is pending"""
        return self.status in ["pending", "processing"]

    @property
    def can_be_cancelled(self) -> bool:
        """Check if withdrawal can be cancelled"""
        return self.status in ["pending"]

    def mark_completed(self):
        """Mark withdrawal as completed"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()

    def mark_failed(self, reason: str = None):
        """Mark withdrawal as failed"""
        self.status = "failed"
        self.failed_at = datetime.utcnow()
        if reason:
            self.failure_reason = reason

    def mark_processing(self):
        """Mark withdrawal as processing"""
        self.status = "processing"
