from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
from datetime import datetime

from app.business.transaction import TransactionService
from app.dependencies import get_db, get_user_except_pending_fpr
from app.models import User
from app.schemas.transaction import (
    TransactionHistoryResponse,
    TransactionResponse,
    TransactionCreate,
    TransactionConfirm,
    TransactionDetailResponse,
    TransactionAccept,
    TransactionDecline, TransactionStatusUpdate
)
from app.schemas.router import TransactionHistoryFilter

router = APIRouter(tags=["Transactions"])


@router.get("/", response_model=TransactionHistoryResponse)
def get_transaction_history(
        filter_params: Annotated[TransactionHistoryFilter, Query()],
        db: Session = Depends(get_db),
        user: User = Depends(get_user_except_pending_fpr)
):
    """
    Get transaction history for the authenticated user with advanced filtering and sorting.

    Supports comprehensive filtering and sorting options:
    - **Date range**: Filter by date_from and date_to
    - **Users**: Filter by specific sender_id or receiver_id
    - **Direction**: Filter by 'in' (received) or 'out' (sent) transactions
    - **Status**: Filter by transaction status (pending, completed, etc.)
    - **Sorting**: Sort by date or amount, ascending or descending
    - **Pagination**: Use limit and offset for pagination

    Returns paginated transaction history with summary statistics including
    total transactions, outgoing total, and incoming total amounts.
    Only COMPLETED transactions are included in financial totals.
    """
    return TransactionService.get_user_transaction_history(db, user, filter_params)


@router.get("/pending/received", response_model=List[TransactionResponse])
def get_pending_received_transactions(db: Session = Depends(get_db),
                                      user: User = Depends(get_user_except_pending_fpr)):
    """
    Get all transactions awaiting acceptance where the user is the receiver.

    Returns only transactions where the sender has confirmed and reserved funds
    (status: AWAITING_ACCEPTANCE). These are actionable transactions that the
    receiver can accept or decline with real financial commitment.

    Note: Does NOT include PENDING transactions (sender created but not confirmed).
    """
    return TransactionService.get_pending_received_transactions(db, user)


@router.get("/pending/sent", response_model=List[TransactionResponse])
def get_pending_sent_transactions(db: Session = Depends(get_db),
                                  user: User = Depends(get_user_except_pending_fpr)):
    """
    Get all pending transactions where the user is the sender.

    Returns transactions that are waiting for sender confirmation.
    These are transactions that the current user can confirm or cancel.
    """
    return TransactionService.get_pending_sent_transactions(db, user)


@router.post("/", response_model=TransactionResponse,
             description="Create a new pending transaction for the authenticated user.")
def create_transaction(transaction_data: TransactionCreate,
                       db: Session = Depends(get_db),
                       user: User = Depends(get_user_except_pending_fpr)):
    """
    Create a new pending transaction.

    Creates a transaction in PENDING status that requires confirmation before
    the actual balance transfer occurs. This allows for validation and gives
    users a chance to review before money is moved.

    :param transaction_data: Data required to create the transaction.
    :param db: The SQLAlchemy session dependency.
    :param user: The currently authenticated user (sender).
    :return: The created pending transaction instance.
    """
    return TransactionService.create_pending_transaction(db, user, transaction_data)


@router.put("/status/{transaction_id}", response_model=TransactionResponse,
             description="Update the status of a transaction.")
def update_transaction_status(transaction_id: int,
                              status: TransactionStatusUpdate,
                              db: Session = Depends(get_db),
                              user: User = Depends(get_user_except_pending_fpr)):
    """
    Update the status of a transaction.
    """
    return TransactionService.update_transaction_status(db, user, transaction_id, status)


@router.get("/{transaction_id}", response_model=TransactionResponse,
            description="Get details of a specific transaction.")
def get_transaction(transaction_id: int,
                    db: Session = Depends(get_db),
                    user: User = Depends(get_user_except_pending_fpr)):
    """
    Get details of a specific transaction.

    Returns transaction details if the authenticated user is either the sender
    or receiver of the transaction. Access is restricted to involved parties only.

    :param transaction_id: ID of the transaction to retrieve.
    :param db: The SQLAlchemy session dependency.
    :param user: The currently authenticated user.
    :return: The transaction details.
    """
    return TransactionService.get_transaction_by_id(db, user, transaction_id)
