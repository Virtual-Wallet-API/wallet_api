from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# Search queries model for user search (admin)

class AdminUserFilter(BaseModel):
    search_by: Optional[Literal["username", "phone", "email"]] = \
        Field(None,
              description="Search all registered users by phone, email or username")

    search_query: Optional[str] = Field(None,
                                        description="The value to search for with the chosen filter")

    limit: int = Field(30, gt=9, le=100, description="The maximum number of results per page")
    page: int = Field(1, ge=1, description="The page you wish to view")


#  Search queries model for user deposits search (user)
class UserDepositsFilter(BaseModel):
    search_by: Optional[Literal["date_period", "amount_range", "status"]] = \
        Field(None,
              description="Filter deposits by date period, amount range or status")
    search_query: Optional[str] = Field(None,
                                        description="The value to search for with the chosen filter ")
    order_by: Literal["asc", "desc"] = \
        Field("desc",
              description="Sort date_period and amount_range by ascending or descending order")

    limit: int = Field(30, gt=9, le=100, description="The maximum number of results per page")
    page: int = Field(1, ge=1, description="The page you wish to view")

class TransactionHistoryFilter(BaseModel):
    # Pagination
    limit: Optional[int] = Field(None, description="Limit number of results")
    offset: Optional[int] = Field(None, description="Offset for pagination")

    # Sorting
    order_by: str = Field("date_desc", description="Sort order: date_desc, date_asc, amount_desc, amount_asc")

    # Date filtering
    date_from: Optional[datetime] = Field(None, description="Filter transactions from this date (ISO format)")
    date_to: Optional[datetime] = Field(None, description="Filter transactions until this date (ISO format)")

    # User filtering
    sender_id: Optional[int] = Field(None, description="Filter by specific sender ID")
    receiver_id: Optional[int] = Field(None, description="Filter by specific receiver ID")

    # Direction filtering
    direction: Optional[str] = Field(None, description="Filter by direction: 'in' for received, 'out' for sent")

    # Status filtering
    status: Optional[str] = Field(None,
                                  description="Filter by transaction status: pending, awaiting_acceptance, completed, denied, cancelled, failed")