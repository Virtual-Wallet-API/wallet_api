from datetime import date, datetime, timedelta
from enum import Enum
from typing import List

from sqlalchemy import Integer, Column, String, Boolean, Float, DateTime, select, union, or_, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates, relationship, Session, Query
from sqlalchemy.sql import Select
from sqlalchemy.types import Enum as CEnum

from app.infrestructure import Base, data_validators
from app.models import Deposit, Card, Transaction
from app.models.deposit import DepositStatus
from app.models.transaction import TransactionStatus
from app.models.withdrawal import Withdrawal, WithdrawalType, WithdrawalStatus


class UserStatus(str, Enum):
    EMAIL = "email_verification"
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
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    balance = Column(Float, nullable=False, default=0)
    reserved_balance = Column(Float, nullable=False, default=0)  # For pending transactions
    admin = Column(Boolean, nullable=False, default=False)
    avatar = Column(String, nullable=True)

    status = Column(CEnum(UserStatus, name="user_status",
                          values_callable=lambda obj: [e.value for e in obj]),
                    nullable=False,
                    default=UserStatus.EMAIL)
    email_key = Column(String, nullable=True)

    forced_password_reset = Column(Boolean, nullable=False, default=False)

    # Stripe integration
    stripe_customer_id = Column(String(255), nullable=True, unique=True)  # Stripe customer ID

    cards = relationship("Card", back_populates="user")
    contacts = relationship("Contact", foreign_keys="[Contact.user_id]", back_populates="user", lazy='dynamic')
    categories = relationship("Category", back_populates="user")
    deposits = relationship("Deposit", back_populates="user")
    withdrawals = relationship("Withdrawal", back_populates="user")

    # Transactions logic

    sent_transactions = relationship("Transaction", foreign_keys="Transaction.sender_id", back_populates="sender", lazy='dynamic')
    received_transactions = relationship("Transaction", foreign_keys="Transaction.receiver_id",
                                         back_populates="receiver", lazy='dynamic')

    @hybrid_property
    def transactions(self):
        # For instance-level access, return list of transactions
        query = select(Transaction).where(
            or_(Transaction.sender_id == self.id, Transaction.receiver_id == self.id)
        ).order_by(Transaction.date.desc())
        return self._session.execute(query).scalars().all()

    @hybrid_property
    def transactions_query(self):
        # Return a Select object for 2.0 compatibility
        return select(Transaction).where(
            or_(Transaction.sender_id == self.id, Transaction.receiver_id == self.id)
        )

    @property
    def pending_received_transactions(self):
        query = select(Transaction).where(
            Transaction.receiver_id == self.id,
            Transaction.status == TransactionStatus.PENDING
        )
        return self._session.execute(query).scalars().all()

    @property
    def pending_sent_transactions(self):
        query = select(Transaction).where(
            Transaction.sender_id == self.id,
            Transaction.status == TransactionStatus.PENDING
        )
        return self._session.execute(query).scalars().all()

    @property
    def awaiting_acceptance_sent_transactions(self):
        query = select(Transaction).where(
            Transaction.sender_id == self.id,
            Transaction.status == TransactionStatus.AWAITING_ACCEPTANCE
        )
        return self._session.execute(query).scalars().all()

    @transactions.expression
    def transactions(cls):
        return select(Transaction).where(
            or_(Transaction.sender_id == cls.id, Transaction.receiver_id == cls.id)
        )

    def get_transactions(self, db: Session, date_from: date = None, date_to: date = None,
                         order_by: str = "date_desc", offset=None, limit=None,
                         legacy_query: bool = True) -> Select | Query:
        """
        Get transactions query with filtering, sorting, and pagination.
        :param db: SQLAlchemy 2.0 Session
        :param date_from: Start date filter
        :param date_to: End date filter
        :param order_by: Sort order ('date_asc', 'date_desc', 'amount_asc', 'amount_desc')
        :param offset: Pagination offset
        :param limit: Pagination limit
        :param legacy_query: Return 1.x Query object for backward compatibility
        :return: SQLAlchemy 2.0 Select or 1.x Query object
        """
        query = self.transactions_query

        if date_from and date_to:
            query = query.filter(Transaction.date.between(date_from, date_to))

        if order_by == "date_asc":
            query = query.order_by(Transaction.date.asc())
        elif order_by == "date_desc":
            query = query.order_by(Transaction.date.desc())
        elif order_by == "amount_asc":
            query = query.order_by(Transaction.amount.asc())
        else:  # amount_desc
            query = query.order_by(Transaction.amount.desc())

        if offset is not None and limit is not None:
            query = query.offset(offset).limit(limit)

        if legacy_query:
            # Convert to 1.x Query for backward compatibility
            return db.query(Transaction).select_from(query.subquery())

        return query

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


    @property
    def months_since_creation(self):
        if not self.created_at:
            return 0
        days = (datetime.now() - self.created_at).days
        return max(1, int(days / 30.42))

    # Deposits and withdrawals properties

    @property
    def is_admin(self) -> bool:
        return self.admin

    @property
    def completed_deposits(self) -> List[Deposit]:
        return [deposit for deposit in self.deposits
                if deposit.status == DepositStatus.COMPLETED]

    @property
    def deposits_per_month(self):
        return round(self.completed_deposits_count / self.months_since_creation, 2)

    @property
    def deposit_avg_monthly(self):
        if self.total_deposit_amount <= 0:
            return 0
        return round(self.total_deposit_amount / self.months_since_creation, 2)

    @property
    def average_deposit_amount(self):
        if self.completed_deposits_count == 0:
            return 0
        return round(self.total_deposit_amount / self.completed_deposits_count, 2)

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

    @property
    def total_withdrawals_last_month(self):
        return sum([1 for w in self.withdrawals
                    if datetime.now() + timedelta(days=2) >= w.completed_at >= datetime.now() - timedelta(days=30)])

    @property
    def total_withdrawn_amount_last_month(self):
        return sum([w.amount for w in self.withdrawals
                    if datetime.now() + timedelta(days=2) >= w.completed_at >= datetime.now() - timedelta(days=30)])

    @property
    def average_last_month(self):
        if self.total_withdrawn_amount_last_month == 0:
            return 0
        return round(self.total_withdrawn_amount_last_month / self.total_withdrawals_last_month, 2)

    @property
    def withdrawal_frequency(self):
        start = self.created_at
        months = 0
        while start < datetime.now():
            months += 1
            start += timedelta(days=30.5)

        return int(len(self.withdrawals) / months)

    # Reserved balance methods for improved transaction flow

    @property
    def available_balance(self) -> float:
        """Get available balance (total balance minus reserved balance)"""
        return self.balance - self.reserved_balance

    def reserve_funds(self, amount: float) -> bool:
        """
        Reserve funds for a pending transaction
        :param amount: Amount to reserve
        :return: True if successful
        :raises: ValueError if insufficient available balance
        """
        if self.available_balance < amount:
            raise ValueError(
                f"Insufficient available balance. Available: ${self.available_balance:.2f}, Required: ${amount:.2f}")

        self.reserved_balance += amount
        return True

    def release_reserved_funds(self, amount: float) -> bool:
        """
        Release reserved funds (when transaction is cancelled or declined)
        :param amount: Amount to release
        :return: True if successful
        """
        if self.reserved_balance < amount:
            raise ValueError(
                f"Cannot release more than reserved. Reserved: ${self.reserved_balance:.2f}, Requested: ${amount:.2f}")

        self.reserved_balance -= amount
        return True

    def transfer_from_reserved(self, amount: float) -> bool:
        """
        Transfer funds from reserved balance to actual balance deduction (when transaction completes)
        :param amount: Amount to transfer
        :return: True if successful
        """
        if self.reserved_balance < amount:
            raise ValueError(
                f"Cannot transfer more than reserved. Reserved: ${self.reserved_balance:.2f}, Requested: ${amount:.2f}")

        if self.balance < amount:
            raise ValueError(f"Insufficient total balance. Balance: ${self.balance:.2f}, Required: ${amount:.2f}")

        # Remove from both reserved and total balance
        self.reserved_balance -= amount
        self.balance -= amount
        return True

    def __repr__(self):
        return f"User(#{self.id}, {self.username}, {self.email})"
