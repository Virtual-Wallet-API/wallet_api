from datetime import datetime

from pydantic_core import core_schema, CoreSchema
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Float, String
from sqlalchemy.orm import relationship
from app.infrestructure import Base
from fastapi import HTTPException
from sqlalchemy.orm import validates


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler) -> CoreSchema:
        return core_schema.str_schema()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(Enum(TransactionStatus.PENDING,
                         TransactionStatus.COMPLETED,
                         TransactionStatus.FAILED,
                         TransactionStatus.CANCELLED,
                         name="status"),
                    default=TransactionStatus.PENDING, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)

    category = relationship("Category", back_populates="transactions")
    recurring_transaction = relationship("RecurringTransaction", back_populates="transaction")
    currency = relationship("Currency", back_populates="transactions")

    @validates("amount")
    def validate_amount(self, key, v: float):
        if v < 0:
            raise HTTPException(status_code=400,
                                detail="Amount must be positive")
        return v

