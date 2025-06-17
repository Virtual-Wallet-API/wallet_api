from app.models.transaction import Transaction
from typing import Dict, Optional
from app.business.utils import NotificationService, NotificationType
from app.business.utils.notification_service import EmailTemplates
import logging

# Set up logging for email notifications
logger = logging.getLogger(__name__)


class TransactionNotificationService:
    """Service for handling transaction email notifications"""

    @staticmethod
    def notify_sender_transaction_created(transaction: Transaction):
        """Notify sender that transaction was created and needs confirmation"""
        try:
            # Send email to sender
            result = NotificationService.notify_from_template(
                template=EmailTemplates.TRANSACTION_CREATED,
                user=transaction.sender,
                amount=transaction.amount,
                recipient_username=transaction.receiver.username,
                description=transaction.description or 'No description',
                transaction_id=transaction.id
            )
            
            # Log the notification
            logger.info(f"Transaction created email sent to {transaction.sender.email} for transaction {transaction.id}")
            
            # Also print to console for development/debugging
            print(f"📧 EMAIL SENT to {transaction.sender.email}: Transaction Created - Confirmation Required")
            print(f"   💰 Transaction ${transaction.amount:.2f} to {transaction.receiver.username}")
            print(f"   🔗 Transaction ID: {transaction.id}")
            
            return result.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send transaction created email to {transaction.sender.email}: {str(e)}")
            print(f"❌ Failed to send email notification: {str(e)}")
            return False

    @staticmethod
    def notify_transaction_received(transaction: Transaction):
        """Notify receiver that a new transaction was created for them"""
        try:
            # Send email to receiver
            result = NotificationService.notify_from_template(
                template=EmailTemplates.TRANSACTION_RECEIVED,
                user=transaction.receiver,
                amount=transaction.amount,
                sender_username=transaction.sender.username,
                description=transaction.description or 'No description'
            )
            
            # Log the notification
            logger.info(f"Transaction received email sent to {transaction.receiver.email} for transaction {transaction.id}")
            
            # Also print to console for development/debugging
            print(f"📧 EMAIL SENT to {transaction.receiver.email}: New Transaction Request Received")
            print(f"   💸 ${transaction.amount:.2f} from {transaction.sender.username}")
            print(f"   🔗 Transaction ID: {transaction.id}")
            
            return result.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send transaction received email to {transaction.receiver.email}: {str(e)}")
            print(f"❌ Failed to send email notification: {str(e)}")
            return False

    @staticmethod
    def notify_sender_transaction_confirmed(transaction: Transaction):
        """Notify sender that transaction was confirmed and funds are reserved"""
        try:
            # Send email to sender
            result = NotificationService.notify_from_template(
                template=EmailTemplates.TRANSACTION_CONFIRMED,
                user=transaction.sender,
                amount=transaction.amount,
                recipient_username=transaction.receiver.username,
                description=transaction.description or 'No description',
                transaction_id=transaction.id
            )
            
            # Log the notification
            logger.info(f"Transaction confirmed email sent to {transaction.sender.email} for transaction {transaction.id}")
            
            # Also print to console for development/debugging
            print(f"📧 EMAIL SENT to {transaction.sender.email}: Transaction Confirmed - Funds Reserved")
            print(f"   ✅ ${transaction.amount:.2f} reserved for {transaction.receiver.username}")
            print(f"   🔗 Transaction ID: {transaction.id}")
            
            return result.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send transaction confirmed email to {transaction.sender.email}: {str(e)}")
            print(f"❌ Failed to send email notification: {str(e)}")
            return False

    @staticmethod
    def notify_transaction_awaiting_acceptance(transaction: Transaction):
        """Notify receiver that transaction is confirmed and awaiting their acceptance"""
        try:
            # Send email to receiver
            result = NotificationService.notify_from_template(
                template=EmailTemplates.TRANSACTION_AWAITING_ACCEPTANCE,
                user=transaction.receiver,
                amount=transaction.amount,
                sender_username=transaction.sender.username,
                description=transaction.description or 'No description',
                transaction_id=transaction.id
            )
            
            # Log the notification
            logger.info(f"Transaction awaiting acceptance email sent to {transaction.receiver.email} for transaction {transaction.id}")
            
            # Also print to console for development/debugging
            print(f"📧 EMAIL SENT to {transaction.receiver.email}: Transaction Ready - Action Required")
            print(f"   🎯 ${transaction.amount:.2f} from {transaction.sender.username} awaiting acceptance")
            print(f"   🔗 Transaction ID: {transaction.id}")
            
            return result.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send transaction awaiting acceptance email to {transaction.receiver.email}: {str(e)}")
            print(f"❌ Failed to send email notification: {str(e)}")
            return False

    @staticmethod
    def notify_sender_transaction_completed(transaction: Transaction):
        """Notify sender that receiver accepted and transaction is completed"""
        try:
            # Send email to sender
            result = NotificationService.notify_from_template(
                template=EmailTemplates.TRANSACTION_COMPLETED_SENDER,
                user=transaction.sender,
                amount=transaction.amount,
                recipient_username=transaction.receiver.username,
                description=transaction.description or 'No description',
                transaction_id=transaction.id
            )
            
            # Log the notification
            logger.info(f"Transaction completed email sent to sender {transaction.sender.email} for transaction {transaction.id}")
            
            # Also print to console for development/debugging
            print(f"📧 EMAIL SENT to {transaction.sender.email}: Transaction Completed Successfully")
            print(f"   🎉 ${transaction.amount:.2f} sent to {transaction.receiver.username}")
            print(f"   🔗 Transaction ID: {transaction.id}")
            
            return result.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send transaction completed email to sender {transaction.sender.email}: {str(e)}")
            print(f"❌ Failed to send email notification: {str(e)}")
            return False

    @staticmethod
    def notify_transaction_completed(transaction: Transaction):
        """Notify receiver that transaction was completed and funds received"""
        try:
            # Send email to receiver
            result = NotificationService.notify_from_template(
                template=EmailTemplates.TRANSACTION_COMPLETED_RECEIVER,
                user=transaction.receiver,
                amount=transaction.amount,
                sender_username=transaction.sender.username,
                description=transaction.description or 'No description',
                transaction_id=transaction.id
            )
            
            # Log the notification
            logger.info(f"Transaction completed email sent to receiver {transaction.receiver.email} for transaction {transaction.id}")
            
            # Also print to console for development/debugging
            print(f"📧 EMAIL SENT to {transaction.receiver.email}: Payment Received Successfully")
            print(f"   💰 +${transaction.amount:.2f} from {transaction.sender.username}")
            print(f"   🔗 Transaction ID: {transaction.id}")
            
            return result.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send transaction completed email to receiver {transaction.receiver.email}: {str(e)}")
            print(f"❌ Failed to send email notification: {str(e)}")
            return False

    @staticmethod
    def notify_transaction_declined(transaction: Transaction, reason: Optional[str] = None):
        """Notify all parties about transaction decline"""
        try:
            # Send email to sender about decline
            sender_result = NotificationService.notify_from_template(
                template=EmailTemplates.TRANSACTION_DECLINED,
                user=transaction.sender,
                amount=transaction.amount,
                recipient_username=transaction.receiver.username,
                description=transaction.description or 'No description',
                transaction_id=transaction.id,
                reason=reason or 'No reason provided'
            )
            
            # Send email to receiver confirming their action
            receiver_result = NotificationService.notify(
                user=transaction.receiver,
                title="Transaction Declined - Confirmation",
                message=f"You have successfully declined the transaction of ${transaction.amount:.2f} from {transaction.sender.username}. Transaction ID: {transaction.id}"
            )
            
            # Log the notifications
            logger.info(f"Transaction declined emails sent for transaction {transaction.id}")
            
            # Also print to console for development/debugging
            print(f"📧 EMAIL SENT to {transaction.sender.email}: Transaction Declined")
            print(f"📧 EMAIL SENT to {transaction.receiver.email}: Transaction Declined - Confirmation")
            print(f"   ❌ ${transaction.amount:.2f} transaction declined")
            print(f"   🔗 Transaction ID: {transaction.id}")
            
            return sender_result.status_code == 200 and receiver_result.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send transaction declined emails for transaction {transaction.id}: {str(e)}")
            print(f"❌ Failed to send email notifications: {str(e)}")
            return False

    @staticmethod
    def notify_transaction_cancelled(transaction: Transaction):
        """Notify all parties about transaction cancellation"""
        try:
            # Send email to sender
            sender_result = NotificationService.notify_from_template(
                template=EmailTemplates.TRANSACTION_CANCELLED,
                user=transaction.sender,
                amount=transaction.amount,
                recipient_username=transaction.receiver.username,
                description=transaction.description or 'No description',
                transaction_id=transaction.id
            )
            
            # Send email to receiver
            receiver_result = NotificationService.notify(
                user=transaction.receiver,
                title="Transaction Cancelled",
                message=f"The transaction of ${transaction.amount:.2f} from {transaction.sender.username} has been cancelled. Transaction ID: {transaction.id}"
            )
            
            # Log the notifications
            logger.info(f"Transaction cancelled emails sent for transaction {transaction.id}")
            
            # Also print to console for development/debugging
            print(f"📧 EMAIL SENT to {transaction.sender.email}: Transaction Cancelled")
            print(f"📧 EMAIL SENT to {transaction.receiver.email}: Transaction Cancelled - Notification")
            print(f"   🚫 ${transaction.amount:.2f} transaction cancelled")
            print(f"   🔗 Transaction ID: {transaction.id}")
            
            return sender_result.status_code == 200 and receiver_result.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send transaction cancelled emails for transaction {transaction.id}: {str(e)}")
            print(f"❌ Failed to send email notifications: {str(e)}")
            return False

    @staticmethod
    def notify_transaction_failed(transaction: Transaction, error_message: str):
        """Notify all parties about transaction failure"""
        try:
            # Send email to sender
            sender_result = NotificationService.notify_from_template(
                template=EmailTemplates.TRANSACTION_FAILED,
                user=transaction.sender,
                amount=transaction.amount,
                recipient_username=transaction.receiver.username,
                description=transaction.description or 'No description',
                transaction_id=transaction.id,
                error_message=error_message
            )
            
            # Send email to receiver
            receiver_result = NotificationService.notify(
                user=transaction.receiver,
                title="Transaction Failed",
                message=f"The transaction of ${transaction.amount:.2f} from {transaction.sender.username} has failed due to: {error_message}. Transaction ID: {transaction.id}"
            )
            
            # Log the notifications
            logger.error(f"Transaction failed emails sent for transaction {transaction.id}: {error_message}")
            
            # Also print to console for development/debugging
            print(f"📧 EMAIL SENT to {transaction.sender.email}: Transaction Failed")
            print(f"📧 EMAIL SENT to {transaction.receiver.email}: Transaction Failed - Notification")
            print(f"   ❌ ${transaction.amount:.2f} transaction failed: {error_message}")
            print(f"   🔗 Transaction ID: {transaction.id}")
            
            return sender_result.status_code == 200 and receiver_result.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send transaction failed emails for transaction {transaction.id}: {str(e)}")
            print(f"❌ Failed to send email notifications: {str(e)}")
            return False

    # Legacy method for backward compatibility
    @classmethod
    def notify_transaction_confirmed(cls, transaction: Transaction) -> bool:
        """Legacy method - now redirects to notify_transaction_completed for compatibility"""
        return cls.notify_transaction_completed(transaction)
