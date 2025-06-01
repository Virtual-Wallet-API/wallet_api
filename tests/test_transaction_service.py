"""
Unit tests for TransactionService business logic.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime

from tests.base_test import BaseTestCase
from app.business.transaction.transaction_service import TransactionService
from app.models import User, Transaction, RecurringTransaction
from app.models.transaction import TransactionStatus, TransactionUpdateStatus
from app.schemas.transaction import TransactionCreate, TransactionStatusUpdate
from app.schemas.router import TransactionHistoryFilter


class TestTransactionService(BaseTestCase):
    """Test cases for TransactionService."""

    def setUp(self):
        super().setUp()
        self.sender = self._create_mock_user(user_id=1, balance=1000.0)
        self.receiver = self._create_mock_user(user_id=2, balance=500.0)
        
        # Mock the balance operations
        self.sender.reserve_funds = Mock()
        self.sender.transfer_from_reserved = Mock()
        self.sender.release_reserved_funds = Mock()

    @patch('app.business.user.user_validators.UserValidators.search_user_by_identifier')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_self_transaction')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_amount')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_sufficient_available_balance')
    @patch('app.business.transaction.transaction_notifications.TransactionNotificationService.notify_sender_transaction_created')
    @patch('app.business.transaction.transaction_notifications.TransactionNotificationService.notify_transaction_received')
    def test_create_pending_transaction_success(self, mock_notify_received, mock_notify_created,
                                              mock_validate_balance, mock_validate_amount,
                                              mock_validate_self, mock_search_user):
        """Test successful creation of a pending transaction."""
        # Arrange
        mock_search_user.return_value = self.receiver
        mock_validate_amount.return_value = 100.0
        
        transaction_data = Mock()
        transaction_data.identifier = 'test@example.com'
        transaction_data.amount = 100.0
        transaction_data.description = 'Test transaction'
        transaction_data.category_id = 1
        transaction_data.currency_id = 1
        transaction_data.recurring = False

        # Act
        result = TransactionService.create_pending_transaction(self.mock_db, self.sender, transaction_data)

        # Assert
        mock_search_user.assert_called_once_with(self.mock_db, 'test@example.com')
        mock_validate_self.assert_called_once_with(self.sender.id, self.receiver.id)
        mock_validate_amount.assert_called_once_with(100.0)
        mock_validate_balance.assert_called_once_with(self.sender, 100.0)
        
        self.assert_db_add_called_with_type(Transaction)
        self.assert_db_operations_called(add=True, commit=True, refresh=True)
        
        mock_notify_created.assert_called_once()
        mock_notify_received.assert_called_once()

    @patch('app.business.user.user_validators.UserValidators.search_user_by_identifier')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_self_transaction')
    def test_create_pending_transaction_self_transaction_error(self, mock_validate_self, mock_search_user):
        """Test creation fails when user tries to send to themselves."""
        # Arrange
        mock_search_user.return_value = self.sender  # Same user
        mock_validate_self.side_effect = HTTPException(status_code=400, detail="Cannot send to yourself")
        
        transaction_data = Mock()
        transaction_data.identifier = 'test@example.com'

        # Act & Assert
        with self.assertRaises(HTTPException):
            TransactionService.create_pending_transaction(self.mock_db, self.sender, transaction_data)

    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_exists')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_ownership')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_confirmable')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_sufficient_available_balance')
    @patch('app.business.transaction.transaction_notifications.TransactionNotificationService.notify_sender_transaction_confirmed')
    @patch('app.business.transaction.transaction_notifications.TransactionNotificationService.notify_transaction_awaiting_acceptance')
    def test_confirm_transaction_success(self, mock_notify_awaiting, mock_notify_confirmed,
                                       mock_validate_balance, mock_validate_confirmable,
                                       mock_validate_ownership, mock_validate_exists):
        """Test successful transaction confirmation."""
        # Arrange
        mock_transaction = self._create_mock_transaction(status=TransactionStatus.PENDING)
        mock_transaction.sender = self.sender
        mock_transaction.recurring = False
        mock_validate_exists.return_value = mock_transaction

        # Act
        result = TransactionService.confirm_transaction(self.mock_db, self.sender, 1)

        # Assert
        mock_validate_exists.assert_called_once_with(1, self.mock_db)
        mock_validate_ownership.assert_called_once_with(mock_transaction, self.sender)
        mock_validate_confirmable.assert_called_once_with(mock_transaction, self.sender)
        mock_validate_balance.assert_called_once_with(self.sender, mock_transaction.amount)
        
        self.sender.reserve_funds.assert_called_once_with(mock_transaction.amount)
        self.assertEqual(mock_transaction.status, TransactionStatus.AWAITING_ACCEPTANCE)
        
        self.assert_db_operations_called(add=False, commit=True, refresh=True)
        mock_notify_confirmed.assert_called_once()
        mock_notify_awaiting.assert_called_once()

    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_exists')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_ownership')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_confirmable')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_sufficient_available_balance')
    def test_confirm_transaction_insufficient_balance_error(self, mock_validate_balance, mock_validate_confirmable,
                                                          mock_validate_ownership, mock_validate_exists):
        """Test transaction confirmation fails with insufficient balance."""
        # Arrange
        mock_transaction = self._create_mock_transaction(status=TransactionStatus.PENDING)
        mock_transaction.sender = self.sender
        mock_transaction.recurring = False
        mock_validate_exists.return_value = mock_transaction
        
        self.sender.reserve_funds.side_effect = ValueError("Insufficient balance")

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            TransactionService.confirm_transaction(self.mock_db, self.sender, 1)
        
        self.assertEqual(context.exception.status_code, 400)

    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_exists')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_acceptable')
    @patch('app.business.transaction.transaction_notifications.TransactionNotificationService.notify_sender_transaction_completed')
    @patch('app.business.transaction.transaction_notifications.TransactionNotificationService.notify_transaction_completed')
    def test_accept_transaction_success(self, mock_notify_completed, mock_notify_sender_completed,
                                      mock_validate_acceptable, mock_validate_exists):
        """Test successful transaction acceptance."""
        # Arrange
        mock_transaction = self._create_mock_transaction(status=TransactionStatus.AWAITING_ACCEPTANCE)
        mock_transaction.sender = self.sender
        mock_transaction.receiver = self.receiver
        mock_transaction.recurring = False
        mock_validate_exists.return_value = mock_transaction

        initial_receiver_balance = self.receiver.balance

        # Act
        result = TransactionService.accept_transaction(self.mock_db, self.receiver, 1)

        # Assert
        mock_validate_exists.assert_called_once_with(1, self.mock_db)
        mock_validate_acceptable.assert_called_once_with(mock_transaction, self.receiver)
        
        self.sender.transfer_from_reserved.assert_called_once_with(mock_transaction.amount)
        self.assertEqual(self.receiver.balance, initial_receiver_balance + mock_transaction.amount)
        self.assertEqual(mock_transaction.status, TransactionStatus.COMPLETED)
        
        self.assert_db_operations_called(add=False, commit=True, refresh=True)
        mock_notify_sender_completed.assert_called_once()
        mock_notify_completed.assert_called_once()

    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_exists')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_acceptable')
    def test_accept_transaction_transfer_error(self, mock_validate_acceptable, mock_validate_exists):
        """Test transaction acceptance fails when transfer fails."""
        # Arrange
        mock_transaction = self._create_mock_transaction(status=TransactionStatus.AWAITING_ACCEPTANCE)
        mock_transaction.sender = self.sender
        mock_transaction.receiver = self.receiver
        mock_transaction.recurring = False
        mock_validate_exists.return_value = mock_transaction
        
        self.sender.transfer_from_reserved.side_effect = ValueError("Transfer failed")

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            TransactionService.accept_transaction(self.mock_db, self.receiver, 1)
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(mock_transaction.status, TransactionStatus.FAILED)

    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_exists')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_declinable')
    @patch('app.business.transaction.transaction_notifications.TransactionNotificationService')
    def test_decline_transaction_success(self, mock_notifications, mock_validate_declinable, mock_validate_exists):
        """Test successful transaction decline."""
        # Arrange
        transaction = self._create_mock_transaction(status=TransactionStatus.AWAITING_ACCEPTANCE)
        transaction.receiver_id = self.receiver.id  # Ensure receiver ownership
        transaction.sender = self.sender  # Set sender for notifications
        transaction.recurring = False  # Ensure it's not a recurring transaction

        # Mock the sender's release_reserved_funds method
        self.sender.release_reserved_funds = Mock()

        mock_validate_exists.return_value = transaction
        mock_validate_declinable.return_value = None  # No validation errors
        mock_notification_service = mock_notifications.return_value
        mock_notification_service.notify_transaction_declined = Mock()

        # Act
        result = TransactionService.decline_transaction(self.mock_db, self.receiver, 1, "Not interested")

        # Assert
        mock_validate_exists.assert_called_once_with(1, self.mock_db)
        mock_validate_declinable.assert_called_once_with(transaction, self.receiver)
        self.sender.release_reserved_funds.assert_called_once_with(transaction.amount)
        self.assertEqual(transaction.status, TransactionStatus.DENIED)
        self.assert_db_operations_called(add=False, commit=True, refresh=True)

    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_exists')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_ownership')
    @patch('app.business.transaction.transaction_notifications.TransactionNotificationService')
    def test_cancel_transaction_success(self, mock_notifications, mock_validate_ownership, mock_validate_exists):
        """Test successful transaction cancellation."""
        # Arrange
        transaction = self._create_mock_transaction(status=TransactionStatus.PENDING)
        transaction.sender_id = self.sender.id  # Ensure sender ownership
        transaction.recurring = False  # Not a recurring transaction

        mock_validate_exists.return_value = transaction
        mock_validate_ownership.return_value = None  # No validation errors
        mock_notification_service = mock_notifications.return_value
        mock_notification_service.notify_transaction_cancelled = Mock()

        # Act
        result = TransactionService.cancel_transaction(self.mock_db, self.sender, 1)

        # Assert
        mock_validate_exists.assert_called_once_with(1, self.mock_db)
        mock_validate_ownership.assert_called_once_with(transaction, self.sender)
        self.assertEqual(transaction.status, TransactionStatus.CANCELLED)
        self.assert_db_operations_called(add=False, commit=True, refresh=True)

    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_exists')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_ownership')
    def test_get_transaction_by_id_success(self, mock_validate_ownership, mock_validate_exists):
        """Test successful retrieval of transaction by ID."""
        # Arrange
        mock_transaction = self._create_mock_transaction()
        mock_validate_exists.return_value = mock_transaction

        # Act
        result = TransactionService.get_transaction_by_id(self.mock_db, self.sender, 1)

        # Assert
        mock_validate_exists.assert_called_once_with(1, self.mock_db)
        mock_validate_ownership.assert_called_once_with(mock_transaction, self.sender)
        self.assertEqual(result, mock_transaction)

    def test_update_transaction_status_routing(self):
        """Test that update_transaction_status routes correctly to specific methods."""
        # Arrange
        status_accept = Mock()
        status_accept.action = TransactionUpdateStatus.ACCEPT

        status_cancel = Mock()
        status_cancel.action = TransactionUpdateStatus.CANCEL

        status_confirm = Mock()
        status_confirm.action = TransactionUpdateStatus.CONFIRM

        status_decline = Mock()
        status_decline.action = TransactionUpdateStatus.DECLINE

        # Test each status update routing
        with patch.object(TransactionService, 'accept_transaction') as mock_accept:
            TransactionService.update_transaction_status(self.mock_db, self.sender, 1, status_accept)
            mock_accept.assert_called_once_with(self.mock_db, self.sender, 1)

        with patch.object(TransactionService, 'cancel_transaction') as mock_cancel:
            TransactionService.update_transaction_status(self.mock_db, self.sender, 1, status_cancel)
            mock_cancel.assert_called_once_with(self.mock_db, self.sender, 1)

        with patch.object(TransactionService, 'confirm_transaction') as mock_confirm:
            TransactionService.update_transaction_status(self.mock_db, self.sender, 1, status_confirm)
            mock_confirm.assert_called_once_with(self.mock_db, self.sender, 1)

        with patch.object(TransactionService, 'decline_transaction') as mock_decline:
            TransactionService.update_transaction_status(self.mock_db, self.sender, 1, status_decline)
            mock_decline.assert_called_once_with(self.mock_db, self.sender, 1)

    def test_get_pending_received_transactions(self):
        """Test retrieval of pending received transactions."""
        # Arrange
        mock_transactions = [
            self._create_mock_transaction(1, status=TransactionStatus.AWAITING_ACCEPTANCE),
            self._create_mock_transaction(2, status=TransactionStatus.AWAITING_ACCEPTANCE)
        ]

        # Mock the user property directly (no database query)
        self.receiver.pending_received_transactions = mock_transactions

        # Act
        result = TransactionService.get_pending_received_transactions(self.mock_db, self.receiver)

        # Assert - No database query, just user property access
        self.assertEqual(result, mock_transactions)

    def test_get_pending_sent_transactions(self):
        """Test retrieval of pending sent transactions."""
        # Arrange
        mock_transactions = [
            self._create_mock_transaction(1, status=TransactionStatus.PENDING),
            self._create_mock_transaction(2, status=TransactionStatus.PENDING)
        ]

        # Mock the user property directly (no database query)
        self.sender.pending_sent_transactions = mock_transactions

        # Act
        result = TransactionService.get_pending_sent_transactions(self.mock_db, self.sender)

        # Assert - No database query, just user property access
        self.assertEqual(result, mock_transactions)

    @patch('app.business.transaction.transaction_service.TransactionService.make_transaction_recurring')
    def test_get_user_transaction_history_with_filters(self, mock_make_recurring):
        """Test retrieval of user transaction history with filters."""
        # Arrange
        mock_transactions = [
            self._create_mock_transaction(1, status=TransactionStatus.COMPLETED),
            self._create_mock_transaction(2, status=TransactionStatus.COMPLETED)
        ]

        # Mock the user.get_transactions method which returns a query object
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_transactions  # Return actual list

        # Mock the user method that returns the query
        self.sender.get_transactions = Mock(return_value=mock_query)

        filter_params = TransactionHistoryFilter(
            date_from=None,
            date_to=None,
            sender_id=None,
            receiver_id=None,
            direction=None,
            status=None,
            limit=10,
            offset=0,
            sort_by='date_desc'
        )

        # Act
        result = TransactionService.get_user_transaction_history(self.mock_db, self.sender, filter_params)

        # Assert
        self.sender.get_transactions.assert_called_once_with(self.mock_db)
        self.assertEqual(len(result.transactions), 2)  # Now len() will work

    def test_handle_status_update_error(self):
        """Test error handling in status updates."""
        # Arrange
        mock_transaction = self._create_mock_transaction()
        mock_transaction.sender = self.sender
        test_error = ValueError("Test error")

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            TransactionService._handle_status_update_error(
                self.mock_db, mock_transaction, test_error, 
                release_funds=True, sender=self.sender
            )
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(mock_transaction.status, TransactionStatus.FAILED)
        self.sender.release_reserved_funds.assert_called_once_with(mock_transaction.amount)
        self.mock_db.rollback.assert_called_once()


if __name__ == '__main__':
    unittest.main() 