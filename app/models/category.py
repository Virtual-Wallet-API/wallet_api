from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Float, String
from sqlalchemy.orm import relationship
from app.infrestructure import Base
from fastapi import HTTPException
from sqlalchemy.orm import validates

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")

    @validates("name")
    def validate_name(self, key, v: str):
        if len(v) < 2:
            raise HTTPException(status_code=400,
                                detail="Name must be at least 2 characters long")
        return v