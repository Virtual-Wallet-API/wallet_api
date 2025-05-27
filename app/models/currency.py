from fastapi import HTTPException
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Enum, Float
from sqlalchemy.orm import relationship, validates

from app.infrestructure import Base


class Currency(Base):
    __tablename__ = 'currencies'
    id = Column(Integer, primary_key=True,autoincrement=True)
    code = Column(String, nullable=False)

    deposits = relationship("Deposit", back_populates="currency")
    transactions = relationship("Transaction", back_populates="currency")
    withdrawals = relationship("Withdrawal", back_populates="currency")
