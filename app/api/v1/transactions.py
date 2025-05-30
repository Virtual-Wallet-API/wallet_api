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
    TransactionDecline
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
    return TransactionService.get_user_transaction_history(
        db=db,
        user=user,
        **filter_params.model_dump()
        )


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


@router.post("/{transaction_id}/confirm", response_model=TransactionResponse,
             description="Confirm a pending transaction and execute the balance transfer.")
def confirm_transaction(transaction_id: int,
                        confirm_data: TransactionConfirm,
                        db: Session = Depends(get_db),
                        user: User = Depends(get_user_except_pending_fpr)):
    """
    Confirm a pending transaction and execute the balance transfer.

    This endpoint validates the transaction, checks current balances, and
    executes the actual money transfer between sender and receiver accounts.
    Only the sender can confirm their own pending transactions.

    :param transaction_id: ID of the transaction to confirm.
    :param confirm_data: Confirmation data (currently empty but allows for future extensions).
    :param db: The SQLAlchemy session dependency.
    :param user: The currently authenticated user.
    :return: The confirmed transaction with updated status.
    """
    return TransactionService.confirm_transaction(db, user, transaction_id)


@router.post("/{transaction_id}/accept", response_model=TransactionResponse,
             description="Accept a pending transaction as the receiver.")
def accept_transaction(transaction_id: int,
                       accept_data: TransactionAccept,
                       db: Session = Depends(get_db),
                       user: User = Depends(get_user_except_pending_fpr)):
    """
    Accept a pending transaction as the receiver.

    This allows the receiver to accept a pending transaction, which immediately
    executes the balance transfer. This is an alternative to sender confirmation.
    Only the receiver can accept transactions sent to them.

    :param transaction_id: ID of the transaction to accept.
    :param accept_data: Acceptance data with optional message.
    :param db: The SQLAlchemy session dependency.
    :param user: The currently authenticated user (receiver).
    :return: The accepted transaction with completed status.
    """
    return TransactionService.accept_transaction(db, user, transaction_id, accept_data.message)


@router.post("/{transaction_id}/decline", response_model=TransactionResponse,
             description="Decline a pending transaction as the receiver.")
def decline_transaction(transaction_id: int,
                        decline_data: TransactionDecline,
                        db: Session = Depends(get_db),
                        user: User = Depends(get_user_except_pending_fpr)):
    """
    Decline a pending transaction as the receiver.

    This allows the receiver to decline a pending transaction, which marks it
    as denied and prevents it from being executed. The sender will be notified.
    Only the receiver can decline transactions sent to them.

    :param transaction_id: ID of the transaction to decline.
    :param decline_data: Decline data with optional reason.
    :param db: The SQLAlchemy session dependency.
    :param user: The currently authenticated user (receiver).
    :return: The declined transaction with denied status.
    """
    return TransactionService.decline_transaction(db, user, transaction_id, decline_data.reason)


@router.post("/{transaction_id}/cancel", response_model=TransactionResponse,
             description="Cancel a pending transaction.")
def cancel_transaction(transaction_id: int,
                       db: Session = Depends(get_db),
                       user: User = Depends(get_user_except_pending_fpr)):
    """
    Cancel a pending transaction.

    Allows the sender to cancel their own pending transaction before it's confirmed.
    Once cancelled, the transaction cannot be confirmed or executed.

    :param transaction_id: ID of the transaction to cancel.
    :param db: The SQLAlchemy session dependency.
    :param user: The currently authenticated user.
    :return: The cancelled transaction with updated status.
    """
    return TransactionService.cancel_transaction(db, user, transaction_id)


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
