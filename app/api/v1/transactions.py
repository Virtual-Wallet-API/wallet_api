from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_user_except_pending_fpr
from app.models import User, Transaction
from app.schemas.transaction import TransactionHistoryResponse, TransactionResponse, TransactionCreate

router = APIRouter(tags=["Transactions"])


@router.get("/", response_model=TransactionHistoryResponse)
def read_transactions(db: Session = Depends(get_db),
                      user: User = Depends(get_user_except_pending_fpr)):
    # TODO: Move to services
    transactions = db.query(Transaction).filter(
        or_(Transaction.sender_id == user.id, Transaction.receiver_id == user.id)).all()

    transaction_history = {
        "transactions": transactions,
        "total": len(transactions),
        "outgoing_total": sum([t.amount for t in transactions if t.sender_id == user.id]),
        "incoming_total": sum([t.amount for t in transactions if t.receiver_id == user.id])
    }

    return transaction_history


@router.post("/", response_model=TransactionResponse)
def send_transaction(transaction_data: TransactionCreate,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_user_except_pending_fpr)):
    # TODO: Move to services and implement proper balance check and change
    if transaction_data.category_id == 0:
        transaction_data.category_id = None
    transaction = Transaction(sender_id=user.id, **transaction_data.model_dump())
    print(transaction)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction
