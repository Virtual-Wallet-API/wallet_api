from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Query
from sqlalchemy.orm import Session

from app.business import WithdrawalService
from app.business.user.user_admin import AdminService
from app.dependencies import get_db, get_current_admin
from app.models import User
from app.schemas import UserPublicResponse
from app.schemas.admin import UpdateUserStatus, ListAllUsersResponse, ListAllUserTransactionsResponse, \
    AdminTransactionResponse
from app.schemas.user import UserResponse
from app.schemas.router import AdminUserFilter
from app.schemas.withdrawal import WithdrawalResponse, WithdrawalUpdate

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
def get_all_users(search_filter: Annotated[AdminUserFilter, Query()],
                  db: Session = Depends(get_db),
                  admin: User = Depends(get_current_admin)):
    """
    Fetches a list of all users in the system, allowing filtering through search functionality by
    phone, email, or username. The results can be paginated and limited in quantity.

    :param db: Database session
    :param admin: Current authenticated admin user
    :param search_filter: Query parameters used to filter results and pagination
    :return: A list of users matching the search criteria and information about pagination
    """
    return AdminService.get_all_users(db, admin, search_filter)


@router.put("/users/{user_id}/status", response_model=None,
            description="Update the status of a user (approve pending user, block or unblock user, and deactivate/reactivate user).")
def update_user_status(user_id: int,
                       update_data: UpdateUserStatus,
                       admin=Depends(get_current_admin),
                       db: Session = Depends(get_db)):
    """
    Updates the provided user's status to active (approve pending user or unblock user), blocked (block user) or deactivated (deactivate user).
    :param update_data: user (username or id), status and (optionally) reason for status change.
    :param admin: the currently logged in admin user (automatically fetched)
    :param db: database sessions (automatically fetched)
    :return: the updated user object
    """
    return AdminService.update_user_status(db, user_id, update_data, admin)


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


@router.put("/transactions/{transaction_id}", response_model=AdminTransactionResponse,
            description="Update the status of a transaction (approve pending transaction, block or unblock transaction, and deactivate/reactivate transaction).")
def deny_pending_transaction(transaction_id: int,
                             db: Session = Depends(get_db),
                             admin: User = Depends(get_current_admin)):
    """
    Update the status of a transaction (approve pending transaction or unblock transaction), block (block transaction) or deactivate (deactivate transaction).
    :param transaction_id: The ID of the transaction to be updated.
    :param db: Database session dependency.
    :param admin: Current authenticated administrator invoking the request.
    :return: The updated transaction object.
    """
    return AdminService.deny_pending_transaction(db, transaction_id, admin)


@router.put("/withdrawal", response_model=WithdrawalResponse)
def update_withdrawal_status(withdrawal_id: int,
                             update_data: WithdrawalUpdate,
                             user: User = Depends(get_current_admin),
                             db: Session = Depends(get_db)):
    """Update withdrawal status and tracking information"""
    return WithdrawalService.update_withdrawal_status(db, user, withdrawal_id, update_data)


@router.put("/users/{user_id}/role", response_model=UserResponse)
def promote_user_to_admin(user_id: int,
                          admin: User = Depends(get_current_admin),
                          db: Session = Depends(get_db)):
    """

    """
    return AdminService.promote_user_to_admin(db, admin, user_id)
