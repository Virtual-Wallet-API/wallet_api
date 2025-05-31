import datetime
from typing import List

from sqlalchemy import and_
from sqlalchemy.orm import Query, Session

from app.business import NotificationService
from app.business.user.user_auth import UserAuthService
from app.business.utils.notification_service import EmailTemplates
from app.infrestructure import SessionLocal
from app.infrestructure.scheduler import schedule_daily_job
from app.models import Transaction, RecurringTransactionHistory, User
from app.models.recurring_transation import RecurringInterval, RecurringTransaction
from app.models.transaction import TransactionStatus


class RecurringService:
    INTERVALS = [
        RecurringInterval.DAILY,
        RecurringInterval.WEEKLY,
        RecurringInterval.MONTHLY
    ]

    @classmethod
    def gen_recurring_transaction_map(cls, t: Transaction, db: Session, rid: int, interval: RecurringInterval):
        """Generate a map of recurring transaction data"""
        last_execution = (db.query(RecurringTransactionHistory)
                          .filter(RecurringTransactionHistory.recurring_transaction_id == t.id)
                          .order_by(RecurringTransactionHistory.execution_date.desc())
                          .first())

        if last_execution:
            last_execution_date = last_execution.execution_date.date()
            days_since = (datetime.date.today() - last_execution_date).days
            if last_execution_date == datetime.date.today():
                add = False
            else:
                match interval:
                    case RecurringInterval.DAILY:
                        add = last_execution_date != datetime.date.today()

                    case RecurringInterval.WEEKLY:
                        add = days_since % 7 == 0

                    case RecurringInterval.MONTHLY:
                        add = days_since % 30 == 0

                    case _:
                        add = False
        else:
            add = True

        if not add:
            return None

        return {"rid": rid,
                "amount": t.amount,
                "date": t.date,
                "sender": t.sender,
                "receiver": t.receiver,
                "currency": t.currency}

    @classmethod
    def transfer_balance(cls, db: Session, sender: User, receiver: User, amount: float):
        try:
            sender.balance -= amount
            receiver.balance += amount
            db.commit()
            return True
        except Exception as e:
            return False

    @classmethod
    def attempt_execute_recurring(cls, db: Session, map: List[dict]):
        return_map_list = []
        for rt in map:
            can_execute = rt["sender"].available_balance >= rt["amount"]
            if not can_execute:
                return_map_list.append({"failed": True, "reason": "Insufficient balance", "map": rt})
                NotificationService.notify_from_template(EmailTemplates.FAILED_RECURRING_TRANSACTION,
                                                         rt["sender"],
                                                         amount=rt["amount"],
                                                         currency=rt["currency"])
                continue

            can_send = UserAuthService.verify_user_can_transact(rt["sender"])
            can_receive = UserAuthService.verify_user_can_transact(rt["receiver"])
            if not can_send or not can_receive:
                return_map_list.append(
                    {"failed": True, "reason": "Account has suspended rights to transact", "map": rt})
                continue

            if cls.transfer_balance(db, rt["sender"], rt["receiver"], rt["amount"]):
                return_map_list.append({"failed": False, "reason": "", "map": rt})
                continue

        return return_map_list

    @classmethod
    def log_recurring_attempts(cls, *attempts, db: Session):
        failed = 0
        completed = 0
        for attempt_map in attempts:
            for attempt in attempt_map:
                log = RecurringTransactionHistory(recurring_transaction_id=attempt["map"]["rid"],
                                                  execution_date=attempt["map"]["date"],
                                                  status=TransactionStatus.FAILED if \
                                                      attempt["failed"] else TransactionStatus.COMPLETED,
                                                  reason=attempt["reason"])
                db.add(log)
                db.commit()
                failed += 1 if attempt["failed"] else 0
                completed += 1 if not attempt["failed"] else 0

        return completed, failed

    @classmethod
    def execute_recurring_transactions(cls):
        """Execute recurring transactions daily"""
        with SessionLocal() as db:

            if not db:
                print("Database connection error, unable to execute recurring transactions.")
                return
            else:
                map_lists = []
                transactions: Query = (db.query(Transaction, RecurringTransaction.id.label("rt_id"))
                                       .join(RecurringTransaction)
                                       .filter(and_(Transaction.recurring == True,
                                                    Transaction.status == TransactionStatus.ACCEPTED,
                                                    RecurringTransaction.is_active == True)))
                for interval in cls.INTERVALS:
                    query = transactions.filter(RecurringTransaction.interval == interval)
                    map_list = [
                        transaction_map
                        for transaction, rid in query
                        if (transaction_map := cls.gen_recurring_transaction_map(transaction, db, rid, interval))
                    ]
                    map_lists.append(map_list)

                print(
                    f"Recurring transactions executed successfully. Total completed: {results[0]}, failed: {results[1]}")

    @classmethod
    def register_recurring_transactions(cls):
        """ Every day at 8AM execute recurring transactions"""
        schedule_daily_job(func=cls.execute_recurring_transactions,
                           hour=8,
                           minute=0,
                           job_id="execute_recurring_transactions")
