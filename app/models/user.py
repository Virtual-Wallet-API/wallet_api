from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import String, Column, DateTime, Integer, Boolean
from sqlalchemy.orm import validates

from app.infrestructure.auth import pwd_context
from app.infrestructure.database import Base


class User(Base):
    __tablename__ = "users"
    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String, nullable=False, index=True, unique=True)
    hashed_password: str = Column(String, nullable=False)
    email: str = Column(String, nullable=False, index=True, unique=True)

    phone: str = Column(String, nullable=True)
    nickname: str = Column(String, nullable=True)
    role: str = Column(String, default="user", nullable=False)
    created_at: str = Column(DateTime, default=datetime.now, nullable=False)
    last_login: str = Column(DateTime, default=datetime.now, nullable=False)

    @validates("username")
    def validate_username(self, key, v: str):
        if len(v) < 3 or len(v) > 20:
            raise HTTPException(status_code=400,
                                detail="Username must be between 3 and 20 characters long")
        if not v.isalnum():
            raise HTTPException(status_code=400, detail="Username must contain only letters and numbers")
        return v

    @validates("email")
    def validate_email(self, key, v: str):
        if "@" not in v or "." not in v:
            raise HTTPException(status_code=400, detail="Email must be valid")
        return v

    def set_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)

    def verify_password(self, password: str):
        return pwd_context.verify(password, self.hashed_password)