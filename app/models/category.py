from fastapi import HTTPException
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

from app.infrestructure import Base


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")

    @validates("name")
    def validate_name(self, key, v: str):
        if len(v) < 2:
            raise HTTPException(status_code=400,
                                detail="Name must be at least 2 characters long")
        return v

    @property
    def total_transactions(self) -> int:
        return len(self.transactions)

    @property
    def completed_tranasctions(self) -> int:
        return len([t for t in self.transactions if t.is_completed])

    @property
    def total_income(self) -> float:
        return sum([t.amount for t in self.transactions if t.is_income(self.user_id)])

    @property
    def total_expense(self) -> float:
        return sum([t.amount for t in self.transactions if t.is_expense(self.user_id)])


    @property
    def total_amount(self) -> float:
        """Return the total amount of money in this category"""
        return sum([t.amount for t in self.transactions])