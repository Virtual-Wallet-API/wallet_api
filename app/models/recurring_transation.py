from enum import Enum

from fastapi import HTTPException
from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates
from sqlalchemy.types import Enum as CEnum

from app.infrestructure import Base


class RecurringInterval(str, Enum):
    DAILY = "day"
    WEEKLY = "week"
    MONTHLY = "month"


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    interval = Column(CEnum(RecurringInterval, name="recurring_interval",
                            values_callable=lambda obj: [e.value for e in obj]),
                      default=RecurringInterval.DAILY, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)

    transaction = relationship("Transaction", back_populates="recurring_transaction")
    history = relationship("RecurringTransactionHistory", back_populates="recurring_transaction", lazy='dynamic')

    @property
    def executions(self) -> int:
        return self.history.count()

    @property
    def total_transferred(self):
        return self.executions * self.transaction.amount

    @property
    def is_executable(self) -> bool:
        return self.transaction.sender.balance >= self.transaction.amount

    def execute_transaction(self) -> bool | str:
        if not self.is_active: "Recurring transaction is currently paused"
        if not self.transaction.receiver.can_receive_payments:
            "Recurring transaction receiver cannot receive payments"
        if not self.is_executable:
            return f"Insufficient balance to execute recurring transaction to {self.transaction.receiver.username}"

        errorMsg = None
        try:
            self.transaction.sender.balance -= self.transaction.amount
            self.transaction.receiver.balance += self.transaction.amount
            self.transaction.sender.save()
            self.transaction.receiver.save()
        except Exception as e:
            self.transaction.sender.rollback()
            self.transaction.receiver.rollback()
            errorMsg = str(e)
        return errorMsg if errorMsg else True
