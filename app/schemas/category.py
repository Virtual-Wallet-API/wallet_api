from typing import Optional, List

from pydantic import BaseModel, field_validator

from app.schemas.transaction import TransactionResponse, CategoryTransactionResponse


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 32:
            raise ValueError('Name must be between 3 and 32 characters long')
        elif not v.isalnum():
            raise ValueError('Name must only contain alphanumeric characters')
        return v

    @field_validator('description')
    def validate_name(cls, v: str) -> str:
        if len(v) > 120:
            raise ValueError('Description must be between 3 and 120 characters long')
        elif not v.replace(",", "").replace(".", "").isalnum():
            raise ValueError('Description must only contain alphanumeric characters')
        return v


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    transactions: List[CategoryTransactionResponse] = []
    total_transactions: int = 0
    total_income: float = 0.0
    total_expense: float = 0.0

    class Config:
        from_attributes = True