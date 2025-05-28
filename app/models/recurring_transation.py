from fastapi import HTTPException
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

from app.infrestructure import Base


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    interval = Column(Integer, nullable=False)
    is_active = Column(Integer, nullable=False, default=True)

    transaction = relationship("Transaction", back_populates="recurring_transaction")

    # TODO add recurring transaction history table to track how many times and when the transaction goes through

    @validates("interval")
    def validate_interval(self, key, v: int):
        if v < 1:
            raise HTTPException(status_code=400,
                                detail="Interval must be positive")
        return v

    @validates("is_active")
    def validate_is_active(self, key, v: int):
        if v not in [0, 1]:
            raise HTTPException(status_code=400,
                                detail="Is Active must be 0 or 1")

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
            # TODO log executions
            self.transaction.sender.save()
            self.transaction.receiver.save()
        except Exception as e:
            self.transaction.sender.rollback()
            self.transaction.receiver.rollback()
            errorMsg = str(e)
        return errorMsg if errorMsg else True
