from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.infrestructure import Base


class Currency(Base):
    __tablename__ = 'currencies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False)

    deposits = relationship("Deposit", back_populates="currency")
    transactions = relationship("Transaction", back_populates="currency")
    withdrawals = relationship("Withdrawal", back_populates="currency")
