from typing import Optional, Literal

from pydantic import BaseModel, Field


# Search queries model for user search (admin)

class AdminUserFilter(BaseModel):
    search_by: Optional[Literal["username", "phone", "email"]] = \
        Field(None,
              description="Search all registered users by phone, email or username")

    search_query: Optional[str] = Field(None,
                                        description="The value to search for in the chosen filter")

    limit: int = Field(30, gt=10, le=100, description="The maximum number of results per page")
    page: int = Field(1, ge=1, description="The page you wish to view")
