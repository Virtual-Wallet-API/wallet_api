from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_user_except_pending_fpr
from app.models import User, Transaction
from app.schemas.transaction import TransactionHistoryResponse, TransactionResponse, TransactionCreate

router = APIRouter(tags=["Transactions"])


@router.get("/", response_model=TransactionHistoryResponse)
def read_transactions(db: Session = Depends(get_db),
                      user: User = Depends(get_user_except_pending_fpr)):
    # TODO: Move to services
    transactions = user.get_transactions(db).all()

    transaction_history = {
        "transactions": transactions,
        "total": len(transactions),
        "outgoing_total": sum([t.amount for t in transactions if t.sender_id == user.id]),
        "incoming_total": sum([t.amount for t in transactions if t.receiver_id == user.id])
    }

    return transaction_history


@router.post("/", response_model=TransactionResponse,
             description="Create a new transaction for the authenticated user.")
def send_transaction(transaction_data: TransactionCreate,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_user_except_pending_fpr)):
    """
    Processes a transaction request, saves it to the database, and returns the created transaction.

    This function handles the creation of a new transaction for the user, taking necessary
    data, dependencies, and ensuring the transaction is saved in the database. It allows
    to set category_id to None if it's explicitly set as 0 in the input data.

    :param transaction_data: Data required to create the transaction.
    :param db: The SQLAlchemy session dependency.
    :param user: The currently authenticated user.
    :return: The completed and persisted transaction instance.
    """
    # TODO: Move to services and implement proper balance check and change
    if transaction_data.category_id == 0:
        transaction_data.category_id = None
    transaction = Transaction(sender_id=user.id, **transaction_data.model_dump())
    print(transaction)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction
