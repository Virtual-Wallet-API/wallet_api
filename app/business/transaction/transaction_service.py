from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import User, Transaction, RecurringTransaction
from app.models.transaction import TransactionStatus, TransactionUpdateStatus
from app.schemas.transaction import TransactionCreate, TransactionHistoryResponse, TransactionStatusUpdate
from .transaction_notifications import TransactionNotificationService
from .transaction_validators import TransactionValidators
from ..user.user_validators import UserValidators
from ...schemas.router import TransactionHistoryFilter


class TransactionService:
    """Business logic for transaction management"""

    @classmethod
    def create_pending_transaction(cls, db: Session,
                                   sender: User,
                                   transaction_data: TransactionCreate) -> Transaction:
        """
        Create a new pending transaction (no balance changes yet)
        :param db: Database session
        :param sender: User sending the transaction
        :param transaction_data: Transaction creation data
        :return: Created transaction object
        """

        receiver = UserValidators.search_user_by_identifier(db, transaction_data.identifier)

        # Validate transaction data
        TransactionValidators.validate_self_transaction(sender.id, receiver.id)
        validated_amount = TransactionValidators.validate_transaction_amount(transaction_data.amount)
        TransactionValidators.validate_sufficient_available_balance(sender, validated_amount)

        # Handle category_id None conversion
        category_id = None if transaction_data.category_id == 0 else transaction_data.category_id

        # Create pending transaction
        transaction = Transaction(
            sender_id=sender.id,
            receiver_id=receiver.id,
            amount=validated_amount,
            description=transaction_data.description,
            category_id=category_id,
            currency_id=transaction_data.currency_id,
            status=TransactionStatus.PENDING,
            recurring=transaction_data.recurring
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        if transaction_data.recurring:
            cls.make_transaction_recurring(db, transaction, transaction_data.interval)

        db.refresh(transaction)

        # Send notifications
        TransactionNotificationService.notify_sender_transaction_created(transaction)
        TransactionNotificationService.notify_transaction_received(transaction)

        return transaction

    @classmethod
    def update_transaction_status(cls, db: Session, user: User, transaction_id: int, status: TransactionStatusUpdate):
        """Router function for updating transaction status"""
        status_update_map = {
            TransactionUpdateStatus.ACCEPT: TransactionService.accept_transaction,
            TransactionUpdateStatus.CANCEL: TransactionService.cancel_transaction,
            TransactionUpdateStatus.CONFIRM: TransactionService.confirm_transaction,
            TransactionUpdateStatus.DECLINE: TransactionService.decline_transaction
        }

        return status_update_map[status.action](db, user, transaction_id)

    @classmethod
    def _handle_status_update_error(cls, db: Session,
                                    transaction: Transaction,
                                    error: Exception,
                                    release_funds: bool = False,
                                    sender: User = None):
        """
        Common error handling for transaction operations
        :param db: Database session
        :param transaction: Transaction object
        :param error: Exception that occurred
        :param release_funds: Whether to release reserved funds
        :param sender: Sender user (needed if release_funds is True)
        :raises: HTTPException or the original exception
        """
        db.rollback()
        # Mark transaction as failed
        transaction.status = TransactionStatus.FAILED

        # Release reserved funds if needed
        if release_funds and sender:
            try:
                sender.release_reserved_funds(transaction.amount)
            except Exception as fund_error:
                # Log the error but continue with marking the transaction as failed
                print(f"Error releasing funds: {str(fund_error)}")

        db.commit()
        db.refresh(transaction)

        # Notify about failure
        TransactionNotificationService.notify_transaction_failed(transaction, str(error))

        if isinstance(error, ValueError):
            print("line 113")
            raise HTTPException(status_code=400, detail=str(error))
        raise error

    @classmethod
    def confirm_transaction(cls, db: Session, user: User, transaction_id: int) -> Transaction:
        """
        Confirm a pending transaction by reserving funds and changing status to AWAITING_ACCEPTANCE
        :param db: Database session
        :param user: User confirming the transaction (sender)
        :param transaction_id: ID of transaction to confirm
        :return: Confirmed transaction object
        """
        # Validate transaction
        transaction = TransactionValidators.validate_transaction_exists(transaction_id, db)
        TransactionValidators.validate_transaction_ownership(transaction, user)
        TransactionValidators.validate_transaction_confirmable(transaction, user)

        if transaction.recurring:
            return cls.confirm_recurring_transaction(db, user, transaction)

        # Re-validate available balance at confirmation time
        db.refresh(user)  # Refresh user to get latest balance
        TransactionValidators.validate_sufficient_available_balance(user, transaction.amount)

        try:
            # Reserve funds from sender's account
            transaction.sender.reserve_funds(transaction.amount)

            # Change status to awaiting acceptance
            transaction.status = TransactionStatus.AWAITING_ACCEPTANCE

            db.commit()
            db.refresh(transaction)

            # Send notifications - transaction is now confirmed but awaiting receiver acceptance
            TransactionNotificationService.notify_sender_transaction_confirmed(transaction)
            TransactionNotificationService.notify_transaction_awaiting_acceptance(transaction)

            return transaction

        except (ValueError, Exception) as e:
            return cls._handle_status_update_error(db, transaction, e)

    @classmethod
    def accept_transaction(cls, db: Session,
                           receiver: User,
                           transaction_id: int,
                           message: Optional[str] = None) -> Transaction:
        """
        Accept a pending transaction as a receiver and execute the actual balance transfer
        :param db: Database session
        :param receiver: User accepting the transaction (receiver)
        :param transaction_id: ID of transaction to accept
        :param message: Optional message from receiver
        :return: Accepted transaction object
        """
        # Validate transaction
        transaction = TransactionValidators.validate_transaction_exists(transaction_id, db)
        TransactionValidators.validate_transaction_acceptable(transaction, receiver)

        if transaction.recurring:
            return cls.accept_recurring_transaction(db, receiver, transaction)

        try:
            # Refresh both users to get latest balances
            db.refresh(transaction.sender)
            db.refresh(receiver)

            # Transfer from reserved funds to actual transfer
            transaction.sender.transfer_from_reserved(transaction.amount)
            receiver.balance += transaction.amount
            transaction.status = TransactionStatus.COMPLETED

            db.commit()
            db.refresh(transaction)

            # Send completion notifications
            TransactionNotificationService.notify_sender_transaction_completed(transaction)
            TransactionNotificationService.notify_transaction_completed(transaction)

            return transaction

        except (ValueError, Exception) as e:
            return cls._handle_status_update_error(db, transaction, e,
                                                   release_funds=True, sender=transaction.sender)

    @classmethod
    def decline_transaction(cls, db: Session, receiver: User, transaction_id: int,
                            reason: Optional[str] = None) -> Transaction:
        """
        Decline a pending transaction as a receiver and release reserved funds
        :param db: Database session
        :param receiver: User declining the transaction (receiver)
        :param transaction_id: ID of transaction to decline
        :param reason: Optional reason for declining
        :return: Declined transaction object
        """
        # Validate transaction
        transaction = TransactionValidators.validate_transaction_exists(transaction_id, db)
        TransactionValidators.validate_transaction_declinable(transaction, receiver)

        if transaction.recurring:
            return cls.cancel_recurring_transaction(db, receiver, transaction)

        try:
            # Release reserved funds back to sender
            transaction.sender.release_reserved_funds(transaction.amount)

            # Mark transaction as denied
            transaction.status = TransactionStatus.DENIED
            db.commit()
            db.refresh(transaction)

            # Send notifications
            TransactionNotificationService.notify_transaction_declined(transaction, reason)

            return transaction

        except (ValueError, Exception) as e:
            # Simple error handling without changing transaction status
            db.rollback()
            if isinstance(e, ValueError):
                print("line 236")
                raise HTTPException(status_code=400, detail=str(e))
            raise e

    @classmethod
    def cancel_transaction(cls, db: Session, user: User, transaction_id: int) -> Transaction:
        """
        Cancel a pending transaction (only works for PENDING status, not AWAITING_ACCEPTANCE)
        :param db: Database session
        :param user: User canceling the transaction
        :param transaction_id: ID of transaction to cancel
        :return: Cancelled transaction object
        """
        transaction = TransactionValidators.validate_transaction_exists(transaction_id, db)
        TransactionValidators.validate_transaction_ownership(transaction, user)

        if transaction.recurring:
            return cls.cancel_recurring_transaction(db, user, transaction)

        # Only sender can cancel their own transaction
        if transaction.sender_id != user.id:
            raise HTTPException(status_code=403, detail="Only the sender can cancel this transaction")

        # Only allow cancellation of PENDING transactions (before confirmation)
        if transaction.status not in (TransactionStatus.PENDING, TransactionStatus.AWAITING_ACCEPTANCE):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel transaction with status: {transaction.status.value}. Only pending and awaiting confirmation transactions can be cancelled."
            )
        print("Cancelling transaction")
        try:
            transaction.status = TransactionStatus.CANCELLED
            user.release_reserved_funds(transaction.amount)

            db.commit()
            db.refresh(transaction)

            # Send notifications
            TransactionNotificationService.notify_transaction_cancelled(transaction)

            return transaction
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to cancel transaction: {str(e)}")

    @classmethod
    def get_transaction_by_id(cls, db: Session, user: User, transaction_id: int) -> Transaction:
        """
        Get a specific transaction by ID (if user has access)
        :param db: Database session
        :param user: User requesting the transaction
        :param transaction_id: ID of transaction to retrieve
        :return: Transaction object
        """
        transaction = TransactionValidators.validate_transaction_exists(transaction_id, db)
        TransactionValidators.validate_transaction_ownership(transaction, user)
        return transaction

    @classmethod
    def get_user_transaction_history(cls, db: Session, user: User,
                                     history_filter: TransactionHistoryFilter) -> TransactionHistoryResponse:
        # Get base Select object from user.get_transactions
        query = user.get_transactions(db, order_by=history_filter.order_by, legacy_query=False)

        date_from = history_filter.date_from
        date_to = history_filter.date_to
        sender_id = history_filter.sender_id
        receiver_id = history_filter.receiver_id
        direction = history_filter.direction
        status = history_filter.status
        # order_by = history_filter.order_by
        limit = history_filter.limit
        offset = (history_filter.page - 1) * limit

        # Apply additional filters
        if date_from:
            query = query.filter(Transaction.date >= date_from)
        if date_to:
            query = query.filter(Transaction.date <= date_to)
        if sender_id:
            query = query.filter(Transaction.sender_id == sender_id)
        if receiver_id:
            query = query.filter(Transaction.receiver_id == receiver_id)
        if direction == "in":
            query = query.filter(Transaction.receiver_id == user.id)
        elif direction == "out":
            query = query.filter(Transaction.sender_id == user.id)
        if status:
            query = query.filter(Transaction.status == status)

        # Calculate total_count before pagination
        total_count_query = select(func.count()).select_from(Transaction).where(query.whereclause)
        total_count = db.execute(total_count_query).scalar() or 0

        # Calculate financial totals in a single query
        completed_query = query.filter(
            Transaction.status.in_([TransactionStatus.COMPLETED, TransactionStatus.AWAITING_ACCEPTANCE]))
        totals_query = select(
            func.sum(Transaction.amount).filter(Transaction.sender_id == user.id).label('outgoing_total'),
            func.count(Transaction.id).filter(Transaction.sender_id == user.id).label('outgoing_count'),
            func.sum(Transaction.amount).filter(Transaction.receiver_id == user.id).label('incoming_total'),
            func.count(Transaction.id).filter(Transaction.receiver_id == user.id).label('incoming_count'),
            func.count(Transaction.id).label('total_completed')
        ).select_from(Transaction).where(completed_query.whereclause)

        result = db.execute(totals_query).first()
        outgoing_total = result.outgoing_total or 0
        outgoing_count = result.outgoing_count or 0
        incoming_total = result.incoming_total or 0
        incoming_count = result.incoming_count or 0
        total_completed = result.total_completed or 0

        # Apply sorting (override get_transactions sorting)
        # if order_by == "date_asc":
        #     query = query.order_by(Transaction.date.asc())
        # elif order_by == "amount_desc":
        #     query = query.order_by(Transaction.amount.desc())
        # elif order_by == "amount_asc":
        #     query = query.order_by(Transaction.amount.asc())
        # else:  # date_desc
        #     query = query.order_by(Transaction.date.desc())

        # Apply pagination
        query = query.offset(offset).limit(limit)
        transactions = db.execute(query).scalars().all()

        # Return response
        return TransactionHistoryResponse(
            transactions=transactions,
            total=total_count,
            total_completed=total_completed,
            pages=(total_count + limit - 1) // limit,
            outgoing_total=outgoing_total,
            avg_outgoing_transaction=round(outgoing_total / outgoing_count, 2) if outgoing_count > 0 else 0,
            incoming_total=incoming_total,
            avg_incoming_transaction=round(incoming_total / incoming_count, 2) if incoming_count > 0 else 0,
            net_total=round(outgoing_total - incoming_total, 2)
        )

    @classmethod
    def get_pending_received_transactions(cls, db: Session, user: User) -> list[Transaction]:
        """
        Get all transactions awaiting acceptance where the user is the receiver
        :param db: Database session
        :param user: User to get pending transactions for
        :return: List of transactions awaiting acceptance where user is receiver
        """
        return user.pending_received_transactions

    @classmethod
    def get_pending_sent_transactions(cls, db: Session, user: User) -> list[Transaction]:
        """
        Get all pending transactions where the user is the sender (before confirmation)
        :param db: Database session
        :param user: User to get pending transactions for
        :return: List of pending transactions where user is sender
        """
        return user.pending_sent_transactions

    @classmethod
    def get_awaiting_acceptance_sent_transactions(cls, db: Session, user: User) -> list[Transaction]:
        """
        Get all transactions awaiting acceptance where the user is the sender (after confirmation)
        :param db: Database session
        :param user: User to get awaiting acceptance transactions for
        :return: List of transactions awaiting acceptance where user is sender
        """
        return user.awaiting_acceptance_sent_transactions

    @classmethod
    def make_transaction_recurring(cls, db, transaction, interval):
        recurring = RecurringTransaction(transaction_id=transaction.id, interval=interval, is_active=False)
        db.add(recurring)
        db.commit()
        db.refresh(recurring)
        db.refresh(transaction)
        return transaction

    @classmethod
    def confirm_recurring_transaction(cls, db, user, transaction):
        if transaction.status != TransactionStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot confirm transaction with status: {transaction.status.value}. Only pending transactions can be confirmed."
            )
        transaction.status = TransactionStatus.ACCEPTED
        db.commit()
        db.refresh(transaction)
        return transaction

    @classmethod
    def accept_recurring_transaction(cls, db, user, transaction):
        if transaction.status != TransactionStatus.AWAITING_ACCEPTANCE:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot accept transaction with status: {transaction.status.value}. Only awaiting confirmation transactions can be accepted."
            )
        recurring = transaction.recurring_transaction
        recurring.is_active = True
        transaction.status = TransactionStatus.ACCEPTED
        db.commit()
        db.refresh(transaction)
        return transaction

    @classmethod
    def cancel_recurring_transaction(cls, db, user, transaction):
        if transaction.status not in (TransactionStatus.AWAITING_ACCEPTANCE, TransactionStatus.PENDING,
                                      TransactionStatus.ACCEPTED):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel transaction with status: {transaction.status.value}. Only pending and awaiting confirmation transactions can be cancelled."
            )
        transaction.status = TransactionStatus.CANCELLED
        transaction.recurring_transaction.is_active = False
        db.commit()
        db.refresh(transaction)
        return transaction
