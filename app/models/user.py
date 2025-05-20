from fastapi import HTTPException
from sqlalchemy import Integer, Column, String, Boolean, Enum, Float
from sqlalchemy.orm import validates, relationship

from app.infrestructure import Base


class User(Base):
    __tablename__ = "users"
    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String, nullable=False, index=True, unique=True)
    hashed_password: str = Column(String, nullable=False)
    email: str = Column(String, nullable=False, index=True, unique=True)
    phone_number: int = Column(Integer, nullable=False, unique=True)
    balance: int = Column(Float, nullable=False, default=0)
    admin: bool = Column(Boolean, nullable=False, default=False)
    avatar: str = Column(String, nullable=True)
    status: int = Column(Enum("blocked",
                              "deactivated",
                              "pending",
                              "active",
                              name="status"), nullable=False, default="pending")

    cards = relationship("Card", back_populates="user")

    @validates("username")
    def validate_username(self, key, v: str):
        if len(v) < 2 or len(v) > 20:
            raise HTTPException(status_code=400,
                                detail="Username must be between 3 and 20 characters long")
        return v

    @validates("password")
    def validate_password(self, key, v: str):
        if len(v) < 8:
            raise HTTPException(status_code=400,
                                detail="Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v) \
                or not any(char.isupper() for char in v) \
                or not all(char.isalnum() for char in v):
            raise HTTPException(status_code=400,
                                detail="""Password must contain at least one digit, 
                                one uppercase letter and one alphanumeric character""")
