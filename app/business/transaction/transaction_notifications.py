from app.models.transaction import Transaction
from typing import Dict, Optional
from app.business.utils import NService, NType


class TransactionNotificationService:
    """Service for handling transaction notifications"""

    @staticmethod
    def notify_sender_transaction_created(transaction: Transaction):
        """Notify sender that transaction was created and needs confirmation"""
        print(f"📱 NOTIFICATION for {transaction.sender_info.username}:")
        print(
            f"   💰 Transaction Created - Please confirm to reserve ${transaction.amount:.2f} for {transaction.receiver_info.username}")
        print(f"   🔗 Transaction ID: {transaction.id}")
        print(f"   📝 Description: {transaction.description or 'No description'}")
        print(f"   ⚠️  Funds will be reserved until receiver accepts/declines")

    @staticmethod
    def notify_transaction_received(transaction: Transaction):
        """Notify receiver that a new transaction was created for them"""
        print(f"📱 NOTIFICATION for {transaction.receiver_info.username}:")
        print(f"   💸 New Transaction Request from {transaction.sender_info.username}")
        print(f"   💰 Amount: ${transaction.amount:.2f}")
        print(f"   📝 Description: {transaction.description or 'No description'}")
        print(f"   ⏳ Waiting for sender to confirm...")

    @staticmethod
    def notify_sender_transaction_confirmed(transaction: Transaction):
        """Notify sender that transaction was confirmed and funds are reserved"""
        print(f"📱 NOTIFICATION for {transaction.sender_info.username}:")
        print(f"   ✅ Transaction Confirmed - ${transaction.amount:.2f} reserved")
        print(f"   🔗 Transaction ID: {transaction.id}")
        print(f"   ⏳ Waiting for {transaction.receiver_info.username} to accept...")
        print(f"   💡 Funds are reserved but not transferred yet")

    @staticmethod
    def notify_transaction_awaiting_acceptance(transaction: Transaction):
        """Notify receiver that transaction is confirmed and awaiting their acceptance"""
        print(f"📱 NOTIFICATION for {transaction.receiver_info.username}:")
        print(f"   🎯 Transaction Ready for Acceptance!")
        print(f"   💰 ${transaction.amount:.2f} from {transaction.sender_info.username}")
        print(f"   📝 Description: {transaction.description or 'No description'}")
        print(f"   ✅ Accept to receive funds or ❌ Decline to reject")
        print(f"   💡 Sender's funds are already reserved")

    @staticmethod
    def notify_sender_transaction_completed(transaction: Transaction):
        """Notify sender that receiver accepted and transaction is completed"""
        print(f"📱 NOTIFICATION for {transaction.sender_info.username}:")
        print(f"   🎉 Transaction Completed Successfully!")
        print(f"   ✅ ${transaction.amount:.2f} sent to {transaction.receiver_info.username}")
        print(f"   💳 Funds transferred from your account")
        print(f"   🔗 Transaction ID: {transaction.id}")

    @staticmethod
    def notify_transaction_completed(transaction: Transaction):
        """Notify receiver that transaction was completed and funds received"""
        print(f"📱 NOTIFICATION for {transaction.receiver_info.username}:")
        print(f"   🎉 Payment Received!")
        print(f"   💰 +${transaction.amount:.2f} from {transaction.sender_info.username}")
        print(f"   📝 Description: {transaction.description or 'No description'}")
        print(f"   💳 Funds added to your account")

    @staticmethod
    def notify_transaction_declined(transaction: Transaction, reason: Optional[str] = None):
        """Notify all parties about transaction decline"""
        # Notify sender about decline
        print(f"📱 NOTIFICATION for {transaction.sender_info.username}:")
        print(f"   ❌ Transaction Declined by {transaction.receiver_info.username}")
        print(f"   💰 ${transaction.amount:.2f} returned to your available balance")
        print(f"   🔗 Transaction ID: {transaction.id}")
        if reason:
            print(f"   📝 Reason: {reason}")

        # Notify receiver about their action
        print(f"📱 NOTIFICATION for {transaction.receiver_info.username}:")
        print(f"   ❌ You declined the transaction from {transaction.sender_info.username}")
        print(f"   💰 Amount: ${transaction.amount:.2f}")
        print(f"   🔗 Transaction ID: {transaction.id}")

    @staticmethod
    def notify_transaction_cancelled(transaction: Transaction):
        """Notify all parties about transaction cancellation"""
        # Notify sender
        print(f"📱 NOTIFICATION for {transaction.sender_info.username}:")
        print(f"   🚫 Transaction Cancelled")
        print(f"   💰 ${transaction.amount:.2f} to {transaction.receiver_info.username}")
        print(f"   🔗 Transaction ID: {transaction.id}")

        # Notify receiver
        print(f"📱 NOTIFICATION for {transaction.receiver_info.username}:")
        print(f"   🚫 Transaction from {transaction.sender_info.username} was cancelled")
        print(f"   💰 Amount: ${transaction.amount:.2f}")
        print(f"   🔗 Transaction ID: {transaction.id}")

    @staticmethod
    def notify_transaction_failed(transaction: Transaction, error_message: str):
        """Notify all parties about transaction failure"""
        # Notify sender
        print(f"📱 NOTIFICATION for {transaction.sender_info.username}:")
        print(f"   ❌ Transaction Failed")
        print(f"   💰 ${transaction.amount:.2f} to {transaction.receiver_info.username}")
        print(f"   🔗 Transaction ID: {transaction.id}")
        print(f"   ⚠️  Error: {error_message}")
        print(f"   💡 Any reserved funds have been released")

        # Notify receiver
        print(f"📱 NOTIFICATION for {transaction.receiver_info.username}:")
        print(f"   ❌ Transaction from {transaction.sender_info.username} failed")
        print(f"   💰 Amount: ${transaction.amount:.2f}")
        print(f"   🔗 Transaction ID: {transaction.id}")

    # Legacy method for backward compatibility
    @staticmethod
    def notify_transaction_confirmed(transaction: Transaction):
        """Legacy method - now redirects to notify_transaction_completed for compatibility"""
        TransactionNotificationService.notify_transaction_completed(transaction)

    @classmethod
    def notify_transaction_received(cls, transaction: Transaction) -> bool:
        """
        Notify receiver when they receive a new pending transaction
        :param transaction: The pending transaction
        :return: Success status
        """
        receiver = transaction.receiver
        sender = transaction.sender

        message = {
            "title": "New Transaction Received",
            "body": f"You have received a pending transaction of ${transaction.amount:.2f} from {sender.username}. "
                    f"Description: {transaction.description or 'No description'}",
            "type": NType.IMPORTANT,
            "transaction_id": transaction.id,
            "action_required": True
        }

        # For now, just log the notification (since email service is commented out)
        print(f"📧 NOTIFICATION to {receiver.email}: {message['title']} - {message['body']}")

        # TODO: When email service is implemented, uncomment:
        # return NService.notify(receiver, message)
        return True

    @classmethod
    def notify_transaction_confirmed(cls, transaction: Transaction) -> bool:
        """
        Notify receiver when transaction is confirmed and money is transferred
        :param transaction: The confirmed transaction
        :return: Success status
        """
        receiver = transaction.receiver
        sender = transaction.sender

        message = {
            "title": "Transaction Completed",
            "body": f"You have received ${transaction.amount:.2f} from {sender.username}. "
                    f"Your new balance has been updated.",
            "type": NType.IMPORTANT,
            "transaction_id": transaction.id
        }

        print(f"📧 NOTIFICATION to {receiver.email}: {message['title']} - {message['body']}")
        return True

    @classmethod
    def notify_transaction_cancelled(cls, transaction: Transaction) -> bool:
        """
        Notify receiver when a pending transaction is cancelled
        :param transaction: The cancelled transaction
        :return: Success status
        """
        receiver = transaction.receiver
        sender = transaction.sender

        message = {
            "title": "Transaction Cancelled",
            "body": f"The pending transaction of ${transaction.amount:.2f} from {sender.username} has been cancelled.",
            "type": NType.UNIMPORTANT,
            "transaction_id": transaction.id
        }

        print(f"📧 NOTIFICATION to {receiver.email}: {message['title']} - {message['body']}")
        return True

    @classmethod
    def notify_sender_transaction_created(cls, transaction: Transaction) -> bool:
        """
        Notify sender when their transaction is created and pending confirmation
        :param transaction: The pending transaction
        :return: Success status
        """
        sender = transaction.sender
        receiver = transaction.receiver

        message = {
            "title": "Transaction Created",
            "body": f"Your transaction of ${transaction.amount:.2f} to {receiver.username} has been created and is pending confirmation. "
                    f"Please confirm to complete the transfer.",
            "type": NType.IMPORTANT,
            "transaction_id": transaction.id,
            "action_required": True
        }

        print(f"📧 NOTIFICATION to {sender.email}: {message['title']} - {message['body']}")
        return True

    @classmethod
    def notify_sender_transaction_confirmed(cls, transaction: Transaction) -> bool:
        """
        Notify sender when their transaction is successfully confirmed
        :param transaction: The confirmed transaction
        :return: Success status
        """
        sender = transaction.sender
        receiver = transaction.receiver

        message = {
            "title": "Transaction Confirmed",
            "body": f"Your transaction of ${transaction.amount:.2f} to {receiver.username} has been successfully completed. "
                    f"Your balance has been updated.",
            "type": NType.IMPORTANT,
            "transaction_id": transaction.id
        }

        print(f"📧 NOTIFICATION to {sender.email}: {message['title']} - {message['body']}")
        return True

    @classmethod
    def notify_transaction_failed(cls, transaction: Transaction, reason: str = None) -> bool:
        """
        Notify sender when their transaction fails
        :param transaction: The failed transaction
        :param reason: Optional reason for failure
        :return: Success status
        """
        sender = transaction.sender
        receiver = transaction.receiver

        failure_reason = f" Reason: {reason}" if reason else ""

        message = {
            "title": "Transaction Failed",
            "body": f"Your transaction of ${transaction.amount:.2f} to {receiver.username} has failed.{failure_reason} "
                    f"No money has been transferred.",
            "type": NType.ALERT,
            "transaction_id": transaction.id
        }

        print(f"📧 NOTIFICATION to {sender.email}: {message['title']} - {message['body']}")
        return True