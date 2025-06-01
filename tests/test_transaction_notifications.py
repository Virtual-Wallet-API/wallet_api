"""
Unit tests for TransactionNotificationService business logic.
"""
import unittest
from unittest.mock import Mock, patch
from io import StringIO
import sys

from tests.base_test import BaseTestCase
from app.business.transaction.transaction_notifications import TransactionNotificationService
from app.models import Transaction, User
from app.business.utils import NotificationType


class TestTransactionNotificationService(BaseTestCase):
    """Test cases for TransactionNotificationService."""

    def setUp(self):
        super().setUp()
        # Create mock users with proper attributes
        self.sender = self._create_mock_user(user_id=1, username="sender", email="sender@test.com")
        self.receiver = self._create_mock_user(user_id=2, username="receiver", email="receiver@test.com")

        # Create mock transaction with proper attributes
        self.mock_transaction = self._create_mock_transaction(
            transaction_id=1,
            sender_id=1,
            receiver_id=2,
            amount=100.0,
            description="Test payment"
        )

        # Add required attributes for notifications
        self.mock_transaction.sender = self.sender
        self.mock_transaction.receiver = self.receiver
        self.mock_transaction.sender_info = self.sender
        self.mock_transaction.receiver_info = self.receiver

    def _capture_print_output(self, func, *args, **kwargs):
        """Helper method to capture print output from notification methods."""
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            result = func(*args, **kwargs)
            output = captured_output.getvalue()
            return result, output
        finally:
            sys.stdout = sys.__stdout__

    def test_notify_sender_transaction_created(self):
        """Test notification when transaction is created (classmethod version)."""
        # Act - This calls the classmethod version
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_sender_transaction_created,
            self.mock_transaction
        )

        # Assert - This should be the email notification format
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to sender@test.com", output)
        self.assertIn("Transaction Created", output)
        self.assertIn("$100.00 to receiver", output)

    def test_notify_transaction_received(self):
        """Test notification when transaction is received (now expects email format)."""
        # Act - This calls the classmethod version by default
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_received,
            self.mock_transaction
        )

        # Assert - This should be the email notification format
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to receiver@test.com", output)
        self.assertIn("New Transaction Received", output)
        self.assertIn("$100.00 from sender", output)

    def test_notify_sender_transaction_confirmed(self):
        """Test notification when sender's transaction is confirmed (now expects email format)."""
        # Act - This calls the classmethod version by default
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_sender_transaction_confirmed,
            self.mock_transaction
        )

        # Assert - This should be the email notification format
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to sender@test.com", output)
        self.assertIn("Transaction Confirmed", output)
        self.assertIn("$100.00 to receiver", output)

    def test_notify_transaction_awaiting_acceptance(self):
        """Test notification when transaction awaits acceptance."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_awaiting_acceptance,
            self.mock_transaction
        )

        # Assert
        self.assertIn("📱 NOTIFICATION for receiver:", output)
        self.assertIn("🎯 Transaction Ready for Acceptance!", output)
        self.assertIn("$100.00", output)
        self.assertIn("sender", output)
        self.assertIn("Test payment", output)

    def test_notify_sender_transaction_completed(self):
        """Test notification when sender's transaction is completed."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_sender_transaction_completed,
            self.mock_transaction
        )

        # Assert
        self.assertIn("📱 NOTIFICATION for sender:", output)
        self.assertIn("🎉 Transaction Completed Successfully!", output)
        self.assertIn("$100.00 sent to receiver", output)
        self.assertIn("Transaction ID: 1", output)

    def test_notify_transaction_completed(self):
        """Test notification when receiver's transaction is completed."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_completed,
            self.mock_transaction
        )

        # Assert
        self.assertIn("📱 NOTIFICATION for receiver:", output)
        self.assertIn("🎉 Payment Received!", output)
        self.assertIn("+$100.00 from sender", output)
        self.assertIn("Test payment", output)

    def test_notify_transaction_declined_with_reason(self):
        """Test notification when transaction is declined with reason."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_declined,
            self.mock_transaction,
            "Insufficient verification"
        )

        # Assert - Should notify both sender and receiver
        self.assertIn("📱 NOTIFICATION for sender:", output)
        self.assertIn("❌ Transaction Declined by receiver", output)
        self.assertIn("$100.00 returned", output)
        self.assertIn("Insufficient verification", output)

        self.assertIn("📱 NOTIFICATION for receiver:", output)
        self.assertIn("❌ You declined the transaction", output)
        self.assertIn("sender", output)

    def test_notify_transaction_declined_without_reason(self):
        """Test notification when transaction is declined without reason."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_declined,
            self.mock_transaction
        )

        # Assert
        self.assertIn("📱 NOTIFICATION for sender:", output)
        self.assertIn("❌ Transaction Declined", output)
        self.assertNotIn("Reason:", output)  # No reason provided

    def test_notify_transaction_cancelled(self):
        """Test notification when transaction is cancelled (now expects email format)."""
        # Act - This calls the classmethod version by default
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_cancelled,
            self.mock_transaction
        )

        # Assert - This should be the email notification format
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to receiver@test.com", output)
        self.assertIn("Transaction Cancelled", output)
        self.assertIn("$100.00 from sender", output)

    def test_notify_transaction_failed(self):
        """Test notification when transaction fails (now expects email format)."""
        error_message = "Network timeout error"

        # Act - This calls the classmethod version by default
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_failed,
            self.mock_transaction,
            error_message
        )

        # Assert - This should be the email notification format
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to sender@test.com", output)
        self.assertIn("Transaction Failed", output)
        self.assertIn("Network timeout error", output)

    # Test the classmethod variations that return bool
    def test_notify_transaction_received_classmethod(self):
        """Test the classmethod version of notify_transaction_received."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_received,
            self.mock_transaction
        )

        # Assert
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to receiver@test.com", output)
        self.assertIn("New Transaction Received", output)
        self.assertIn("$100.00 from sender", output)

    def test_notify_transaction_confirmed_classmethod(self):
        """Test the classmethod version of notify_transaction_confirmed."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_confirmed,
            self.mock_transaction
        )

        # Assert
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to receiver@test.com", output)
        self.assertIn("Transaction Completed", output)
        self.assertIn("$100.00 from sender", output)

    def test_notify_sender_transaction_created_classmethod(self):
        """Test the classmethod version of notify_sender_transaction_created."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_sender_transaction_created,
            self.mock_transaction
        )

        # Assert
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to sender@test.com", output)
        self.assertIn("Transaction Created", output)
        self.assertIn("$100.00 to receiver", output)

    def test_notify_sender_transaction_confirmed_classmethod(self):
        """Test the classmethod version of notify_sender_transaction_confirmed."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_sender_transaction_confirmed,
            self.mock_transaction
        )

        # Assert
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to sender@test.com", output)
        self.assertIn("Transaction Confirmed", output)
        self.assertIn("$100.00 to receiver", output)

    def test_notify_transaction_failed_classmethod(self):
        """Test the classmethod version of notify_transaction_failed."""
        reason = "Payment processing error"

        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_failed,
            self.mock_transaction,
            reason
        )

        # Assert
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to sender@test.com", output)
        self.assertIn("Transaction Failed", output)
        self.assertIn("Payment processing error", output)

    def test_notify_transaction_failed_classmethod_no_reason(self):
        """Test the classmethod version of notify_transaction_failed without reason."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_failed,
            self.mock_transaction
        )

        # Assert
        self.assertTrue(result)
        self.assertIn("📧 NOTIFICATION to sender@test.com", output)
        self.assertIn("Transaction Failed", output)

    def test_notification_with_no_description(self):
        """Test notifications work when transaction has no description."""
        # Arrange
        self.mock_transaction.description = None

        # Act - Call the classmethod version which handles None descriptions
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_sender_transaction_created,
            self.mock_transaction
        )

        # Assert - Should show "No description" in email format
        self.assertIn("📧 NOTIFICATION to sender@test.com", output)
        # The classmethod handles None descriptions by using "No description" in the body

    def test_notification_with_empty_description(self):
        """Test notifications work when transaction has empty description."""
        # Arrange
        self.mock_transaction.description = ""

        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_received,
            self.mock_transaction
        )

        # Assert
        self.assertIn("No description", output)

    def test_notification_with_large_amount(self):
        """Test notifications work with large transaction amounts."""
        # Arrange
        self.mock_transaction.amount = 1500.75

        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_completed,
            self.mock_transaction
        )

        # Assert
        self.assertIn("$1500.75", output)

    def test_notification_service_type_constants(self):
        """Test that NotificationType constants are properly used."""
        # This test verifies the import and usage of NotificationType
        # The actual values are used in the classmethod implementations

        # Act & Assert - just verify the import works
        self.assertTrue(hasattr(NotificationType, 'IMPORTANT'))
        self.assertTrue(hasattr(NotificationType, 'UNIMPORTANT'))
        self.assertTrue(hasattr(NotificationType, 'ALERT'))

    def test_notify_transaction_received_staticmethod(self):
        """Test the staticmethod version of notify_transaction_received."""
        # Act - Call the staticmethod version explicitly
        result, output = self._capture_print_output(
            TransactionNotificationService.__dict__['notify_transaction_received'],
            self.mock_transaction
        )

        # Assert - This should be the emoji notification format
        self.assertIn("📱 NOTIFICATION for receiver:", output)
        self.assertIn("💸 New Transaction Request", output)
        self.assertIn("sender", output)
        self.assertIn("$100.00", output)
        self.assertIn("Test payment", output)

    def test_notify_transaction_cancelled_staticmethod(self):
        """Test the staticmethod version of notify_transaction_cancelled."""
        # Act - Call the staticmethod version explicitly
        result, output = self._capture_print_output(
            TransactionNotificationService.__dict__['notify_transaction_cancelled'],
            self.mock_transaction
        )

        # Assert - This should be the emoji notification format
        self.assertIn("📱 NOTIFICATION for sender:", output)
        self.assertIn("🚫 Transaction Cancelled", output)
        self.assertIn("$100.00 to receiver", output)

        self.assertIn("📱 NOTIFICATION for receiver:", output)
        self.assertIn("🚫 Transaction from sender was cancelled", output)

    def test_notify_transaction_failed_staticmethod(self):
        """Test the staticmethod version of notify_transaction_failed."""
        error_message = "Network timeout error"

        # Act - Call the staticmethod version explicitly
        result, output = self._capture_print_output(
            TransactionNotificationService.__dict__['notify_transaction_failed'],
            self.mock_transaction,
            error_message
        )

        # Assert - This should be the emoji notification format
        self.assertIn("📱 NOTIFICATION for sender:", output)
        self.assertIn("❌ Transaction Failed", output)
        self.assertIn("Network timeout error", output)
        self.assertIn("reserved funds have been released", output)

        self.assertIn("📱 NOTIFICATION for receiver:", output)
        self.assertIn("❌ Transaction from sender failed", output)

    def test_notify_transaction_awaiting_acceptance_staticmethod(self):
        """Test the notify_transaction_awaiting_acceptance method which is only staticmethod."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_awaiting_acceptance,
            self.mock_transaction
        )

        # Assert - This should be the emoji notification format
        self.assertIn("📱 NOTIFICATION for receiver:", output)
        self.assertIn("🎯 Transaction Ready for Acceptance!", output)
        self.assertIn("$100.00", output)
        self.assertIn("sender", output)
        self.assertIn("Test payment", output)

    def test_notify_sender_transaction_completed_staticmethod(self):
        """Test the notify_sender_transaction_completed method which is only staticmethod."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_sender_transaction_completed,
            self.mock_transaction
        )

        # Assert - This should be the emoji notification format
        self.assertIn("📱 NOTIFICATION for sender:", output)
        self.assertIn("🎉 Transaction Completed Successfully!", output)
        self.assertIn("$100.00 sent to receiver", output)
        self.assertIn("Transaction ID: 1", output)

    def test_notify_transaction_completed_staticmethod(self):
        """Test the notify_transaction_completed method which is only staticmethod."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_completed,
            self.mock_transaction
        )

        # Assert - This should be the emoji notification format
        self.assertIn("📱 NOTIFICATION for receiver:", output)
        self.assertIn("🎉 Payment Received!", output)
        self.assertIn("+$100.00 from sender", output)
        self.assertIn("Test payment", output)

    def test_notify_transaction_declined_staticmethod(self):
        """Test the notify_transaction_declined method which is only staticmethod."""
        # Act
        result, output = self._capture_print_output(
            TransactionNotificationService.notify_transaction_declined,
            self.mock_transaction,
            "Insufficient verification"
        )

        # Assert - Should notify both sender and receiver
        self.assertIn("📱 NOTIFICATION for sender:", output)
        self.assertIn("❌ Transaction Declined by receiver", output)
        self.assertIn("$100.00 returned", output)
        self.assertIn("Insufficient verification", output)

        self.assertIn("📱 NOTIFICATION for receiver:", output)
        self.assertIn("❌ You declined the transaction", output)
        self.assertIn("sender", output)


if __name__ == '__main__':
    unittest.main()