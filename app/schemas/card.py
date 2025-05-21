from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.schemas import UserPrivateResponse


class CardBase(BaseModel):
    number: str
    expiration_date: datetime
    balance: float = 0

    @field_validator('number')
    def number_must_be_16_digits(cls, v):
        if len(v) != 16:
            raise ValueError('Number must be 16 digits long')
        return v[-4:]

class CardCreate(CardBase):
    design: str
    cardholder: str

    class Config:
        from_attributes = True

class CardPrivateResponse(CardBase):
    id: int
    user: ['UserPrivateResponse']
    balance: float

class CardUpdate(CardBase):
    design: Optional[str] = None


