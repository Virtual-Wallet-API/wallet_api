from typing import Optional, Literal

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
