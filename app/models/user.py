from enum import Enum
from typing import List

from sqlalchemy import Integer, Column, String, Boolean, Float
from sqlalchemy.orm import validates, relationship
from sqlalchemy.types import Enum as CEnum

from app.infrestructure import Base, data_validators
from app.models import Deposit, Card
from app.models.deposit import DepositStatus
from app.models.withdrawal import Withdrawal, WithdrawalType, WithdrawalStatus


class UserStatus(str, Enum):
    BLOCKED = "blocked"
    DEACTIVATED = "deactivated"
    REACTIVATION = "reactivation"
    PENDING = "pending"
    ACTIVE = "active"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, nullable=False, index=True, unique=True)
    hashed_password = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True, unique=True)
    phone_number = Column(String, nullable=False, unique=True)
    balance = Column(Float, nullable=False, default=0)
    admin = Column(Boolean, nullable=False, default=False)
    avatar = Column(String, nullable=True)

    status = Column(CEnum(UserStatus, name="user_status",
                          values_callable=lambda obj: [e.value for e in obj]),
                    nullable=False,
                    default=UserStatus.PENDING)

    forced_password_reset = Column(Boolean, nullable=False, default=False)

    # Stripe integration
    stripe_customer_id = Column(String(255), nullable=True, unique=True)  # Stripe customer ID

    cards = relationship("Card", back_populates="user")
    contacts = relationship("Contact", foreign_keys="[Contact.user_id]", back_populates="user")
    categories = relationship("Category", back_populates="user")
    deposits = relationship("Deposit", back_populates="user")
    withdrawals = relationship("Withdrawal", back_populates="user")

    # Validators

    @validates("username")
    def validate_username(self, key, v: str) -> str:
        return data_validators.validate_username(v)

    @validates("email")
    def validate_email(self, key, v: str) -> str:
        return data_validators.validate_email(v)

    @validates("phone_number")
    def validate_phone_number(self, key, v: str) -> str:
        return data_validators.validate_phone_number(v)

    # Relationships properties

    @property
    def cards_count(self) -> int:
        return len(self.cards)

    @property
    def contacts_count(self) -> int:
        return len(self.contacts)

    @property
    def categories_count(self) -> int:
        return len(self.categories)

    @property
    def deposits_count(self) -> int:
        return len(self.deposits)

    @property
    def withdrawals_count(self) -> int:
        return len(self.withdrawals)

    # Deposits and withdrawals properties

    @property
    def is_admin(self) -> bool:
        return self.admin

    @property
    def completed_deposits(self) -> List[Deposit]:
        return [deposit for deposit in self.deposits
                if deposit.status == DepositStatus.COMPLETED]

    @property
    def completed_deposits_count(self) -> int:
        return len(self.completed_deposits)

    @property
    def completed_withdrawals(self) -> List[Deposit]:
        return [withdrawal for withdrawal in self.withdrawals if withdrawal.is_completed]

    @property
    def total_deposit_amount(self) -> float:
        return sum([deposit.amount for deposit in self.completed_deposits])

    @property
    def total_withdrawal_amount(self) -> float:
        return sum([withdrawal.amount for withdrawal in self.completed_withdrawals])

    @property
    def pending_deposits(self) -> List[Deposit]:
        return [deposit for deposit in self.deposits
                if deposit.status == DepositStatus.PENDING]

    @property
    def pending_deposits_count(self) -> int:
        return len(self.pending_deposits)

    @property
    def pending_withdrawals(self) -> List[Withdrawal]:
        return [withdrawal for withdrawal in self.withdrawals if withdrawal.status == WithdrawalStatus.PENDING]

    @property
    def total_pending_withdrawal_amount(self) -> float:
        return sum([withdrawal.amount for withdrawal in self.pending_withdrawals])

    @property
    def total_pending_deposit_amount(self) -> float:
        return sum([deposit.amount for deposit in self.pending_deposits])

    @property
    def failed_deposits(self) -> List[Deposit]:
        return [deposit for deposit in self.deposits
                if deposit.status in (DepositStatus.FAILED, DepositStatus.CANCELLED)]

    @property
    def failed_deposits_count(self) -> int:
        return len(self.failed_deposits)

    @property
    def total_failed_deposits_amount(self) -> float:
        return sum([deposit.amount for deposit in self.failed_deposits])

    @property
    def failed_withdrawals(self) -> List[Withdrawal]:
        return [withdrawal for withdrawal in self.withdrawals if withdrawal.status == WithdrawalStatus.FAILED]

    @property
    def total_failed_withdrawal_amount(self) -> float:
        return sum([withdrawal.amount for withdrawal in self.failed_withdrawals])

    @property
    def active_cards(self) -> List[Card]:
        return [card for card in self.cards if card.is_active]

    @property
    def deactivated_cards(self) -> List[Card]:
        return [card for card in self.cards if not card.is_active]

    @property
    def refunds(self) -> list["Withdrawal"]:
        """Get all refunds for this withdrawal"""
        return [withdrawal for withdrawal in self.withdrawals
                if withdrawal.withdrawal_type == WithdrawalType.REFUND]

    @property
    def payouts(self) -> list["Withdrawal"]:
        """Get all payouts for this withdrawal"""
        return [withdrawal for withdrawal in self.withdrawals
                if withdrawal.withdrawal_type == WithdrawalType.PAYOUT]

    def __repr__(self):
        return f"User(#{self.id}, {self.username}, {self.email})"
