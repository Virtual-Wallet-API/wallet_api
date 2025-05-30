from datetime import datetime
from pydantic import BaseModel
from app.models.transaction import TransactionStatus

class RecurringTransactionHistoryBase(BaseModel):
    recurring_transaction_id: int
    execution_date: datetime
    status: TransactionStatus


class RecurringTransactionHistoryResponse(RecurringTransactionHistoryBase):
    id: int

    class Config:
        from_attributes = True