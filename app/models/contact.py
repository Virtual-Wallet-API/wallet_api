from fastapi import HTTPException
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

from app.infrestructure import Base
from app.models.transaction import Transaction


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", foreign_keys=[user_id], back_populates="contacts")
    contact_user = relationship("User", foreign_keys=[contact_id])

    @validates("contact_id")
    def validate_contact(self, key, contact_id):
        if self.user_id == contact_id:
            raise HTTPException(status_code=400,
                                detail="You cannot add yourself as a contact")
        return contact_id

    @validates("user_id")
    def validate_user_id(self, key, user_id):
        if not user_id:
            raise HTTPException(status_code=400,
                                detail="User ID is required")
        return user_id

    @property
    def transactions(self):
        return (self.user.transactions_query
                .filter(Transaction.sender_id == self.contact_id or Transaction.receiver_id == self.contact_id).all())
