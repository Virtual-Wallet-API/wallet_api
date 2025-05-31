from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.business.user.user_validators import UserValidators
from app.models import User, Contact
from app.schemas.contact import ContactCreate


class UserContacts:

    @classmethod
    def insert_contact(cls, db: Session, user: User, contact: User) -> Contact:
        db_contact = Contact(user_id=user.id, contact_id=contact.id)
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact

    @classmethod
    def check_contact_exists(cls, db: Session, user: User, contact: User) -> bool:
        return db.query(Contact).filter(Contact.user_id == user.id,
                                        Contact.contact_id == contact.id).first() is not None

    @classmethod
    def add_contact(cls, db: Session, user: User, identifier: ContactCreate) -> Contact:
        identifier = identifier.identifier.strip()

        contact = UserValidators.search_user_by_identifier(db, identifier)
        if cls.check_contact_exists(db, user, contact):
            raise HTTPException(status_code=400, detail="Contact already exists")
        return cls.insert_contact(db, user, contact)

    @classmethod
    def remove_contact(cls, db: Session, user: User, contact_id: int):
        contact = user.contacts.filter(Contact.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        db.delete(contact)
        db.commit()
        return contact
