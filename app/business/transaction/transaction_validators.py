from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models import User, Transaction
from app.models.transaction import TransactionStatus
from app.business.user import UVal


class TransactionValidators:
    """Validation logic for transactions"""

    @staticmethod
    def validate_transaction_amount(amount: float) -> float:
        """
        Validate transaction amount
        :param amount: Transaction amount to validate
        :return: Validated amount
        :raises HTTPException: If amount is invalid
        """
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Transaction amount must be positive")

        if amount > 999999.99:  # Set reasonable upper limit
            raise HTTPException(status_code=400, detail="Transaction amount exceeds maximum limit")

        # Round to 2 decimal places for currency precision
        return round(amount, 2)

    @staticmethod
    def validate_sufficient_available_balance(sender: User, amount: float) -> bool:
        """
        Validate that sender has sufficient available balance (excluding reserved funds)
        :param sender: User sending the transaction
        :param amount: Transaction amount
        :return: True if sufficient available balance
        :raises HTTPException: If insufficient available balance
        """
        if sender.available_balance < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient available balance. Available: ${sender.available_balance:.2f}, Required: ${amount:.2f}"
            )
        return True

    @staticmethod
    def validate_sufficient_balance(sender: User, amount: float) -> bool:
        """
        Validate that sender has sufficient total balance for transaction
        :param sender: User sending the transaction
        :param amount: Transaction amount
        :return: True if sufficient balance
        :raises HTTPException: If insufficient balance
        """
        if sender.balance < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. Available: ${sender.balance:.2f}, Required: ${amount:.2f}"
            )
        return True

    @staticmethod
    def validate_receiver_exists(receiver_id: int, db: Session) -> User:
        """
        Validate that receiver exists and can receive transactions
        :param receiver_id: ID of the receiving user
        :param db: Database session
        :return: Receiver User object
        :raises HTTPException: If receiver doesn't exist or can't receive
        """
        receiver = UVal.find_user_with_or_raise_exception("id", receiver_id, db)

        # Check if receiver can receive payments (not blocked/deactivated)
        if receiver.status in ["blocked", "deactivated"]:
            raise HTTPException(
                status_code=400,
                detail="Recipient cannot receive transactions at this time"
            )

        return receiver

    @staticmethod
    def validate_self_transaction(sender_id: int, receiver_id: int) -> bool:
        """
        Validate that user is not sending money to themselves
        :param sender_id: Sender user ID
        :param receiver_id: Receiver user ID
        :return: True if valid
        :raises HTTPException: If trying to send to self
        """
        if sender_id == receiver_id:
            raise HTTPException(status_code=400, detail="Cannot send money to yourself")
        return True

    @staticmethod
    def validate_transaction_exists(transaction_id: int, db: Session) -> Transaction:
        """
        Validate that transaction exists
        :param transaction_id: Transaction ID
        :param db: Database session
        :return: Transaction object
        :raises HTTPException: If transaction doesn't exist
        """
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction

    @staticmethod
    def validate_transaction_ownership(transaction: Transaction, user: User) -> bool:
        """
        Validate that user owns or is involved in the transaction
        :param transaction: Transaction object
        :param user: User object
        :return: True if user is involved
        :raises HTTPException: If user not involved in transaction
        """
        if transaction.sender_id != user.id and transaction.receiver_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied to this transaction")
        return True

    @staticmethod
    def validate_transaction_confirmable(transaction: Transaction, user: User) -> bool:
        """
        Validate that transaction can be confirmed by the user (sender)
        :param transaction: Transaction object
        :param user: User object
        :return: True if confirmable
        :raises HTTPException: If transaction cannot be confirmed
        """
        if transaction.status != TransactionStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Transaction cannot be confirmed. Current status: {transaction.status}"
            )

        if transaction.sender_id != user.id:
            raise HTTPException(status_code=403, detail="Only the sender can confirm this transaction")

        return True

    @staticmethod
    def validate_receiver_action_allowed(transaction: Transaction, user: User) -> bool:
        """
        Validate that receiver can accept/decline the transaction
        :param transaction: Transaction object
        :param user: User object (receiver)
        :return: True if receiver action is allowed
        :raises HTTPException: If receiver action not allowed
        """
        if transaction.status != TransactionStatus.AWAITING_ACCEPTANCE:
            raise HTTPException(
                status_code=400,
                detail=f"Transaction cannot be accepted/declined. Current status: {transaction.status}. Transaction must be confirmed by sender first."
            )

        if transaction.receiver_id != user.id:
            raise HTTPException(status_code=403, detail="Only the receiver can accept/decline this transaction")

        return True

    @staticmethod
    def validate_transaction_declinable(transaction: Transaction, user: User) -> bool:
        """
        Validate that transaction can be declined by the receiver
        :param transaction: Transaction object
        :param user: User object (receiver)
        :return: True if declinable
        :raises HTTPException: If transaction cannot be declined
        """
        TransactionValidators.validate_receiver_action_allowed(transaction, user)
        return True

    @staticmethod
    def validate_transaction_acceptable(transaction: Transaction, user: User) -> bool:
        """
        Validate that transaction can be accepted by the receiver
        :param transaction: Transaction object
        :param user: User object (receiver)
        :return: True if acceptable
        :raises HTTPException: If transaction cannot be accepted
        """
        TransactionValidators.validate_receiver_action_allowed(transaction, user)

        # No need to check sender balance again since funds are already reserved
        return True
