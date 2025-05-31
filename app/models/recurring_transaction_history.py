from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Enum as CEnum
from sqlalchemy.orm import relationship
from app.infrestructure import Base
from app.models.transaction import TransactionStatus

class RecurringTransactionHistory(Base):
    __tablename__ = "recurring_transaction_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_date = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(CEnum(TransactionStatus, name="transaction_status",
                          values_callable=lambda obj: [e.value for e in obj]),
                    default=TransactionStatus.PENDING,
                    nullable=False)
    reason = Column(String, nullable=True)

    recurring_transaction_id = Column(Integer, ForeignKey("recurring_transactions.id"), nullable=False)

    recurring_transaction = relationship("RecurringTransaction", back_populates="history")