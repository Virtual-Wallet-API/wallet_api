from datetime import datetime
from enum import Enum

from fastapi import HTTPException
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String
from sqlalchemy import Enum as CEnum
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

from app.infrestructure import Base


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.now, nullable=False)

    status = Column(CEnum(TransactionStatus, name="transaction_status",
                          values_callable=lambda obj: [e.value for e in obj]),
                    default=TransactionStatus.PENDING,
                    nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)

    category = relationship("Category", back_populates="transactions")
    recurring_transaction = relationship("RecurringTransaction", back_populates="transaction")
    currency = relationship("Currency", back_populates="transactions")

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_transactions")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_transactions")

    @validates("amount")
    def validate_amount(self, key, v: float):
        if v < 0:
            raise HTTPException(status_code=400,
                                detail="Amount must be positive")
        return v
