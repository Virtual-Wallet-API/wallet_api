from sqlalchemy import Integer, Column, String, Boolean, Enum, Float
from sqlalchemy.orm import validates, relationship

from app.infrestructure import Base
from app.infrestructure.validators import validate_username, validate_password, validate_phone_number


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, index=True, unique=True)
    hashed_password = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True, unique=True)
    phone_number = Column(String, nullable=False, unique=True)
    balance = Column(Float, nullable=False, default=0)
    admin = Column(Boolean, nullable=False, default=False)
    avatar = Column(String, nullable=True)
    status = Column(Enum("blocked", "deactivated", "pending", "active", name="status"),
                         nullable=False, default="pending")

    cards = relationship("Card", back_populates="user")
    contacts = relationship("Contact", foreign_keys="[Contact.user_id]", back_populates="user")

    @validates("username")
    def validate_username(self, key, v: str):
        return validate_username(v)

    @validates("hashed_password")
    def validate_password(self, key, v: str):
        return validate_password(v)

    @validates("phone_number")
    def validate_phone_number(self, key, v: str):
        return validate_phone_number(v)
