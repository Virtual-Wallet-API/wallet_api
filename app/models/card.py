from fastapi import HTTPException
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Enum, Float
from sqlalchemy.orm import relationship, validates

from app.infrestructure import Base


class Card(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    number = Column(Integer, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    balance = Column(Float, nullable=False, default=0)
    cardholder = Column(String, nullable=False)
    cvv = Column(Integer, nullable=False)
    type = Column(Enum("credit", "debit", name="card_type"), nullable=False)
    design = Column(String, nullable=False, default='{"color": "purple"}')

    user = relationship("User", back_populates="cards")

    @validates("number")
    def validate_number(self, key, v: str):
        if len(v) != 16:
            raise HTTPException(status_code=400,
                                detail="Number must be 16 digits long")
        return v

    @validates("cvv")
    def validate_cvv(self, key, v: str):
        if len(v) != 3:
            raise HTTPException(status_code=400,
                                detail="CVV must be 3 digits long")