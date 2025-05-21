from pydantic import BaseModel, field_validator
from typing import Optional

class ContactBase(BaseModel):
    contact_id: int

class ContactCreate(ContactBase):
    user_id: int

    @field_validator("contact_id")
    def validate_not_self(cls, contact_id, values):
        user_id = values.get("user_id")
        if user_id == contact_id:
            raise ValueError("You cannot add yourself as a contact")
        return contact_id

    class Config:
        from_attributes = True