from fastapi import HTTPException
from sqlalchemy.orm import Session

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
    def add_contact(cls, db: Session, user: User, identifier: ContactCreate) -> Contact:
        identifier = identifier.identifier.strip()
        print(identifier)
        if identifier.isnumeric() and len(identifier) == 10:
            contact = db.query(User).filter(User.phone_number == identifier).first()
            if not contact:
                print("No user found matching the provided phone number")
                raise HTTPException(status_code=404, detail="No user found matching the provided phone number")
            return UserContacts.insert_contact(db, user, contact)
        else:
            contact = db.query(User).filter(User.username == identifier).first()
            if not contact:
                contact = db.query(User).filter(User.email == identifier).first()
                if not contact: 
                    raise HTTPException(status_code=404, detail="No user found matching the provided username/email")
            return UserContacts.insert_contact(db, user, contact)

    @classmethod
    def remove_contact(cls, db: Session, user: User, contact_id: int):
        contact = user.contacts.filter(Contact.id == contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        db.delete(contact)
        db.commit()
        return contact
