from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from app.infrestructure import Base
from fastapi import HTTPException
from sqlalchemy.orm import validates

class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    interval = Column(Integer, nullable=False)
    is_active = Column(Integer, nullable=False, default=True)

    transaction = relationship("Transaction", back_populates="recurring_transaction")

    @validates("interval")
    def validate_interval(self, key, v: int):
        if v < 1:
            raise HTTPException(status_code=400,
                                detail="Interval must be positive")
        return v
    @validates("is_active")
    def validate_is_active(self, key, v: int):
        if v not in [0, 1]:
            raise HTTPException(status_code=400,
                                detail="Is Active must be 0 or 1")