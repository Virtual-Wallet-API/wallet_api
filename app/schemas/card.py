from datetime import datetime
from enum import Enum
from typing import Optional, List, ForwardRef

from pydantic import BaseModel, field_validator

UserResponse = ForwardRef("UserResponse")

class CardBase(BaseModel):
    number: str
    cardholder: str
    expiration_date: datetime



    @field_validator('number')
    def number_must_be_16_digits(cls, v):
        if len(v) != 16:
            raise ValueError('Number must be 16 digits long')
        return v[-4:]


class CardType(Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class CardCreate(CardBase):
    design: str
    type: CardType
    cvv: int


class CardPrivateResponse(CardBase):
    id: int
    user: UserResponse

class CardPublicResponse(CardBase):
    id: int
    type: CardType
    design: str

    @field_validator('number')
    def last_four_digits(cls, v):
        return v[-4:]
    class Config:
        from_attributes = True


class CardUpdate(CardBase):
    design: Optional[str] = None

CardPublicResponse.model_rebuild()