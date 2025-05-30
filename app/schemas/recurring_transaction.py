from pydantic import BaseModel


class RecurringTransactionBase(BaseModel):
    transaction_id: int
    interval: int
    is_active: bool
