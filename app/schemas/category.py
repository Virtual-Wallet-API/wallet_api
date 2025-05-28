from typing import Optional, List, Dict, Any

from pydantic import BaseModel, field_validator

from app.schemas.transaction import CategoryTransactionResponse


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
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) > 120:
            raise ValueError('Description must be between 3 and 120 characters long')
        elif not v.replace(",", "").replace(".", "").replace(" ", "").isalnum():
            raise ValueError('Description must only contain alphanumeric characters, commas, periods, and spaces')
        return v


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    """Schema for updating an existing category"""
    pass

class CategoryResponse(CategoryBase):
    id: int
    transactions: List[CategoryTransactionResponse] = []
    total_transactions: int = 0
    total_income: float = 0.0
    total_expense: float = 0.0

    class Config:
        from_attributes = True


class CategoryDetailResponse(CategoryResponse):
    """Schema for detailed category response including transactions"""
    transactions: List[CategoryTransactionResponse] = []

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    """Schema for paginated category list response"""
    categories: List[CategoryResponse]
    total_count: int
    returned_count: int
    total_income: float
    total_expense: float
    total_transactions: int
    has_more: bool


class CategoryStatisticsResponse(BaseModel):
    """Schema for category statistics response"""
    category: CategoryResponse
    statistics: Dict[str, Any]


class CategorySummaryItem(BaseModel):
    """Schema for category summary item"""
    id: int
    name: str
    total_income: Optional[float] = None
    total_expense: Optional[float] = None
    transaction_count: int
    total_amount: Optional[float] = None


class CategorySummaryResponse(BaseModel):
    """Schema for categories summary response"""
    total_categories: int
    total_income: float
    total_expense: float
    net_amount: float
    top_income_categories: List[CategorySummaryItem]
    top_expense_categories: List[CategorySummaryItem]
    most_used_categories: List[CategorySummaryItem]