from datetime import datetime
from enum import Enum

from fastapi import HTTPException
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Boolean, Text
from sqlalchemy import Enum as CEnum
from sqlalchemy.orm import relationship, validates

from app.infrestructure import Base


class CardType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"
    UNKNOWN = "unknown"


class Card(Base):
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Stripe-related fields
    stripe_payment_method_id = Column(String(255), nullable=False, unique=True)  # Stripe payment method ID
    stripe_customer_id = Column(String(255), nullable=True)  # Stripe customer ID (if different from user's)
    stripe_card_fingerprint = Column(String(255), nullable=True)

    # Safe card information (no sensitive data)
    last_four = Column(String(4), nullable=False)  # Last 4 digits only
    brand = Column(String(50), nullable=False)  # visa, mastercard, amex, etc.
    exp_month = Column(Integer, nullable=False)  # Expiration month
    exp_year = Column(Integer, nullable=False)  # Expiration year
    cardholder_name = Column(String(255), nullable=False)

    # Card metadata
    type = Column(CEnum(CardType, name="card_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False,
                  default=CardType.UNKNOWN)
    design = Column(Text, nullable=False, default='{"color": "purple"}')  # JSON string for card design
    is_default = Column(Boolean, default=False)  # Whether this is the user's default card
    is_active = Column(Boolean, default=True)  # Whether the card is active

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="cards")
    deposits = relationship("Deposit", back_populates="card")
    withdrawals = relationship("Withdrawal", back_populates="card")

    @validates("last_four")
    def validate_last_four(self, key, v: str):
        if len(v) != 4 or not v.isdigit():
            raise HTTPException(status_code=400,
                                detail="Last four must be exactly 4 digits")
        return v

    @validates("exp_month")
    def validate_exp_month(self, key, v: int):
        if not (1 <= v <= 12):
            raise HTTPException(status_code=400,
                                detail="Expiration month must be between 1 and 12")
        return v

    @validates("exp_year")
    def validate_exp_year(self, key, v: int):
        current_year = datetime.now().year
        if v < current_year:
            raise HTTPException(status_code=400,
                                detail="Expiration year cannot be in the past")
        return v

    @property
    def masked_number(self) -> str:
        """Return a masked card number for display"""
        return f"**** **** **** {self.last_four}"

    @property
    def is_expired(self) -> bool:
        """Check if the card is expired"""
        now = datetime.now()
        return (self.exp_year < now.year) or (self.exp_year == now.year and self.exp_month < now.month)

    def __repr__(self):
        return f"<{self.type.capitalize()} Card #{self.id} | {self.brand.upper()} ****{self.last_four} | {self.user.username if self.user else 'Unknown'}>"
