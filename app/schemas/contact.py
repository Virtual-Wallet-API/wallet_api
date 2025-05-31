from typing import Optional, ForwardRef

from pydantic import BaseModel

UserPublicResponse = ForwardRef("UserPublicResponse")


class ContactBase(BaseModel):
    identifier: str


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    contact_id: Optional[int] = None


class ContactResponse(ContactBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class ContactPublicResponse(ContactBase):
    id: int
    contact_user: "UserPublicResponse"

    class Config:
        from_attributes = True

# class ContactCreate(ContactBase):
#     contact_id: int
#
#     @field_validator("contact_id")
#     def validate_not_self(cls, contact_id, values):
#         user_id = values.get("user_id")
#         if user_id == contact_id:
#             raise ValueError("You cannot add yourself as a contact")
#         return contact_id
#
#     class Config:
#         from_attributes = True
