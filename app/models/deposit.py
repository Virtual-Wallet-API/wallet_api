from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from app.infrestructure import Base
from fastapi import HTTPException
from sqlalchemy.orm import validates


class Deposit(Base):
    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    type = Column(Enum("credit", "debit", name="card_type"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)

    user = relationship("User", back_populates="deposits")
    currency = relationship("Currency", back_populates="deposits")
    card= relationship("Card", back_populates="deposits")

    @validates("amount")
    def validate_amount(self, key, v: float):
        if v < 0:
            raise HTTPException(status_code=400,
                                detail="Amount must be positive")
        return v



