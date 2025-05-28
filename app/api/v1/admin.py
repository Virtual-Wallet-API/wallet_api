from fastapi import APIRouter, Depends
from fastapi.params import Query
from sqlalchemy.orm import Session

from app.business.user.user_admin import AdminService
from app.dependencies import get_db, get_current_admin
from app.models import User
from app.schemas import UserPublicResponse
from app.schemas.admin import UpdateUserStatus, ListAllUsersResponse, ListAllUserTransactionsResponse

router = APIRouter(tags=["Admin"])


@router.get("/", response_model=UserPublicResponse,
            description="Get information about your admin profile.")
def admin_root(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """
    Get information about your admin profile.
    :param db: database session
    :param admin: your profile as User object
    :return: information about your admin profile
    """
    return admin


@router.get("/users", response_model=ListAllUsersResponse,
            description="Get a list of all users in the system and search by phone, email or username.")
def get_all_users(db: Session = Depends(get_db),
                  admin: User = Depends(get_current_admin),
                  search_by: str = Query(default=None, description="Search by phone, email or username", alias="sb"),
                  search_query: str = Query(default=None, description="Search query", alias="q"),
                  limit: int = Query(default=30, description="Limit the number of results",
                                     alias="l"),
                  page: int = Query(default=1, description="Page number/results offset", alias="p")):
    """
    Fetches a list of all users in the system, allowing filtering through search functionality by
    phone, email, or username. The results can be paginated and limited in quantity.

    :param db: Database session
    :param admin: Current authenticated admin user
    :param search_by: Filter criteria for the search. Can be one of "phone", "email", or "username"
    :param search_query: The actual query string to match with the search_by criterion
    :param limit: Maximum number of user results to be returned in one page. Default is 30
    :param page: Page number or offset for paginated results. Default is page 1
    :return: A list of users matching the search criteria and information about pagination
    """
    search_data = {
        "search_by": search_by,
        "search_query": search_query,
        "limit": limit,
        "page": page
    }
    return AdminService.get_all_users(db, admin, search_data)


@router.put("/users/status", response_model=None,
            description="Update the status of a user (approve pending user, block or unblock user, and deactivate/reactivate user).")
def update_user_status(update_data: UpdateUserStatus,
                       admin=Depends(get_current_admin),
                       db: Session = Depends(get_db)):
    """
    Updates the provided user's status to active (approve pending user or unblock user), blocked (block user) or deactivated (deactivate user).
    :param update_data: user (username or id), status and (optionally) reason for status change.
    :param admin: the currently logged in admin user (automatically fetched)
    :param db: database sessions (automatically fetched)
    :return: the updated user object
    """
    return AdminService.update_user_status(db, update_data, admin)


@router.get("/transactions/{user_id}", response_model=ListAllUserTransactionsResponse,
            description="Get a list of all transactions for a specific user with pagination and sorting options.")
def get_user_transactions(user_id: int,
                          db: Session = Depends(get_db),
                          admin: User = Depends(get_current_admin),
                          search_by: str = Query(default=None,
                                                 description="Search by period, receiver, sender, direction.",
                                                 alias="sb"),
                          search_query: str = Query(default=None, description="Search query", alias="q"),
                          limit: int = Query(default=30, description="Limit the number of results", alias="l"),
                          page: int = Query(default=1, description="Page number/results offset", alias="p"),
                          order_by: str = Query(default="date_dec",
                                                description="Sort results by date_desc, date_asc, amount_desc, amount_desc",
                                                alias="ob")):
    """
    Get a list of all transactions for a specific user with pagination and sorting options.
    :param user_id: The ID of the user whose transactions are being queried.
    :param db: Database session dependency.
    :param admin: Current authenticated administrator invoking the request.
    :param search_by: Filtering criterion to search the transactions. Valid options
                      include period, receiver, sender, or direction.
    :param search_query: The query value related to the filtering criterion. Period format is YYYY-MM-DD_YYYY-MM-DD,
                      direction search includes 'outgoing' and 'incoming' transactions.
    :param limit: The maximum number of transactions to retrieve per page.
    :param page: The page number to retrieve results from, for paginated responses.
    :param order_by: The field to sort the results by. Valid options include
                      date_desc, date_asc, amount_desc, amount_asc.
    :return: A response containing the list of transactions matching the filters as
             well as pagination details.
    """
    search_data = {
        "user_id": user_id,
        "search_by": search_by,
        "search_query": search_query,
        "limit": limit,
        "page": page,
        "order_by": order_by
    }
    return AdminService.get_user_transactions(db, admin, search_data)
