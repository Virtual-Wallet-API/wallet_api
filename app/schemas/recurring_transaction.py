from typing import Literal

from pydantic import BaseModel

from app.models.recurring_transation import RecurringInterval


class RecurringTransactionBase(BaseModel):
    transaction_id: int
    interval: RecurringInterval = RecurringInterval.DAYLY
    is_active: bool = False


class RecurringTransactionResponse(RecurringTransactionBase):
    id: int
    repeated: int = 0
    total_transferred: float = 0.0

    class Config:
        from_attributes = True
