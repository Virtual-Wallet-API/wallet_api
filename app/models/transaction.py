from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from app.infrestructure import Base
from fastapi import HTTPException
from sqlalchemy.orm import validates


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(Enum("pending", "completed", "failed", name="status"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    category = relationship("Category", back_populates="transactions")
    recurring_transaction = relationship("RecurringTransaction", back_populates="transaction")

    @validates("amount")
    def validate_amount(self, key, v: float):
        if v < 0:
            raise HTTPException(status_code=400,
                                detail="Amount must be positive")
        return v

