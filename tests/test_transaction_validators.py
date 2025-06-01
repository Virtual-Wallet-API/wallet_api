"""
Unit tests for TransactionValidators business logic.
"""
import unittest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from tests.base_test import BaseTestCase
from app.business.transaction.transaction_validators import TransactionValidators
from app.models import User, Transaction
from app.models.transaction import TransactionStatus


class TestTransactionValidators(BaseTestCase):
    """Test cases for TransactionValidators."""

    def setUp(self):
        super().setUp()
        self.sender = self._create_mock_user(user_id=1, balance=1000.0)
        self.receiver = self._create_mock_user(user_id=2, balance=500.0)
        self.blocked_user = self._create_mock_user(user_id=3, status="blocked")
        self.deactivated_user = self._create_mock_user(user_id=4, status="deactivated")

        # Add available_balance property to sender
        self.sender.available_balance = 800.0  # Some funds reserved

    def test_validate_transaction_amount_success(self):
        """Test successful amount validation with valid amounts."""
        # Test normal amounts
        result = TransactionValidators.validate_transaction_amount(100.0)
        self.assertEqual(result, 100.0)

        result = TransactionValidators.validate_transaction_amount(50.25)
        self.assertEqual(result, 50.25)

        # Test rounding to 2 decimal places
        result = TransactionValidators.validate_transaction_amount(99.999)
        self.assertEqual(result, 100.0)

        # Test maximum valid amount
        result = TransactionValidators.validate_transaction_amount(999999.99)
        self.assertEqual(result, 999999.99)

    def test_validate_transaction_amount_zero_or_negative(self):
        """Test amount validation fails with zero or negative amounts."""
        # Test zero amount
        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_transaction_amount(0.0)
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("must be positive", context.exception.detail)

        # Test negative amount
        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_transaction_amount(-50.0)
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("must be positive", context.exception.detail)

    def test_validate_transaction_amount_exceeds_maximum(self):
        """Test amount validation fails when exceeding maximum limit."""
        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_transaction_amount(1000000.0)
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("exceeds maximum limit", context.exception.detail)

    def test_validate_sufficient_available_balance_success(self):
        """Test successful available balance validation."""
        result = TransactionValidators.validate_sufficient_available_balance(self.sender, 500.0)
        self.assertTrue(result)

        # Test exact available balance
        result = TransactionValidators.validate_sufficient_available_balance(self.sender, 800.0)
        self.assertTrue(result)

    def test_validate_sufficient_available_balance_insufficient(self):
        """Test available balance validation fails with insufficient funds."""
        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_sufficient_available_balance(self.sender, 900.0)
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Insufficient available balance", context.exception.detail)
        self.assertIn("Available: $800.00", context.exception.detail)
        self.assertIn("Required: $900.00", context.exception.detail)

    def test_validate_sufficient_balance_success(self):
        """Test successful total balance validation."""
        result = TransactionValidators.validate_sufficient_balance(self.sender, 500.0)
        self.assertTrue(result)

        # Test exact balance
        result = TransactionValidators.validate_sufficient_balance(self.sender, 1000.0)
        self.assertTrue(result)

    def test_validate_sufficient_balance_insufficient(self):
        """Test total balance validation fails with insufficient funds."""
        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_sufficient_balance(self.sender, 1500.0)
        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Insufficient balance", context.exception.detail)
        self.assertIn("Available: $1000.00", context.exception.detail)
        self.assertIn("Required: $1500.00", context.exception.detail)

    @patch('app.business.user.user_validators.UserValidators.find_user_with_or_raise_exception')
    def test_validate_receiver_exists_success(self, mock_find_user):
        """Test successful receiver validation with active user."""
        mock_find_user.return_value = self.receiver

        result = TransactionValidators.validate_receiver_exists(2, self.mock_db)

        self.assertEqual(result, self.receiver)
        mock_find_user.assert_called_once_with("id", 2, self.mock_db)

    @patch('app.business.user.user_validators.UserValidators.find_user_with_or_raise_exception')
    def test_validate_receiver_exists_blocked_user(self, mock_find_user):
        """Test receiver validation fails with blocked user."""
        mock_find_user.return_value = self.blocked_user

        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_receiver_exists(3, self.mock_db)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("cannot receive transactions", context.exception.detail)

    @patch('app.business.user.user_validators.UserValidators.find_user_with_or_raise_exception')
    def test_validate_receiver_exists_deactivated_user(self, mock_find_user):
        """Test receiver validation fails with deactivated user."""
        mock_find_user.return_value = self.deactivated_user

        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_receiver_exists(4, self.mock_db)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("cannot receive transactions", context.exception.detail)

    def test_validate_self_transaction_success(self):
        """Test successful self-transaction validation with different users."""
        result = TransactionValidators.validate_self_transaction(1, 2)
        self.assertTrue(result)

    def test_validate_self_transaction_same_user(self):
        """Test self-transaction validation fails when same user."""
        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_self_transaction(1, 1)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Cannot send money to yourself", context.exception.detail)

    def test_validate_transaction_exists_success(self):
        """Test successful transaction existence validation."""
        mock_transaction = self._create_mock_transaction(1)
        query_mock = self.setup_db_query_mock(Transaction, mock_transaction)
        query_mock.first.return_value = mock_transaction

        result = TransactionValidators.validate_transaction_exists(1, self.mock_db)

        self.assertEqual(result, mock_transaction)
        self.mock_db.query.assert_called_with(Transaction)

    def test_validate_transaction_exists_not_found(self):
        """Test transaction existence validation fails when transaction not found."""
        query_mock = self.setup_db_query_mock(Transaction, [])
        query_mock.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_transaction_exists(999, self.mock_db)

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("Transaction not found", context.exception.detail)

    def test_validate_transaction_ownership_sender(self):
        """Test successful transaction ownership validation for sender."""
        mock_transaction = self._create_mock_transaction(sender_id=1, receiver_id=2)

        result = TransactionValidators.validate_transaction_ownership(mock_transaction, self.sender)
        self.assertTrue(result)

    def test_validate_transaction_ownership_receiver(self):
        """Test successful transaction ownership validation for receiver."""
        mock_transaction = self._create_mock_transaction(sender_id=1, receiver_id=2)

        result = TransactionValidators.validate_transaction_ownership(mock_transaction, self.receiver)
        self.assertTrue(result)

    def test_validate_transaction_ownership_unauthorized(self):
        """Test transaction ownership validation fails for unauthorized user."""
        mock_transaction = self._create_mock_transaction(sender_id=1, receiver_id=2)
        unauthorized_user = self._create_mock_user(user_id=999)

        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_transaction_ownership(mock_transaction, unauthorized_user)

        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("Access denied", context.exception.detail)

    def test_validate_transaction_confirmable_success(self):
        """Test successful transaction confirmation validation."""
        mock_transaction = self._create_mock_transaction(sender_id=1, status=TransactionStatus.PENDING)

        result = TransactionValidators.validate_transaction_confirmable(mock_transaction, self.sender)
        self.assertTrue(result)

    def test_validate_transaction_confirmable_wrong_user(self):
        """Test transaction confirmation validation fails for non-sender."""
        mock_transaction = self._create_mock_transaction(sender_id=1, status=TransactionStatus.PENDING)

        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_transaction_confirmable(mock_transaction, self.receiver)

        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("Only the sender can confirm", context.exception.detail)

    def test_validate_transaction_confirmable_wrong_status(self):
        """Test transaction confirmation validation fails for wrong status."""
        mock_transaction = self._create_mock_transaction(sender_id=1, status=TransactionStatus.COMPLETED)

        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_transaction_confirmable(mock_transaction, self.sender)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("cannot be confirmed", context.exception.detail)
        self.assertIn("Current status:", context.exception.detail)

    def test_validate_receiver_action_allowed_success(self):
        """Test successful receiver action validation."""
        mock_transaction = self._create_mock_transaction(
            sender_id=1,
            receiver_id=2,
            status=TransactionStatus.AWAITING_ACCEPTANCE
        )

        result = TransactionValidators.validate_receiver_action_allowed(mock_transaction, self.receiver)
        self.assertTrue(result)

    def test_validate_receiver_action_allowed_wrong_status(self):
        """Test receiver action validation fails for wrong status."""
        mock_transaction = self._create_mock_transaction(
            sender_id=1,
            receiver_id=2,
            status=TransactionStatus.PENDING
        )

        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_receiver_action_allowed(mock_transaction, self.receiver)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("cannot be accepted/declined", context.exception.detail)

    def test_validate_receiver_action_allowed_wrong_user(self):
        """Test receiver action validation fails for non-receiver."""
        mock_transaction = self._create_mock_transaction(
            sender_id=1,
            receiver_id=2,
            status=TransactionStatus.AWAITING_ACCEPTANCE
        )

        with self.assertRaises(HTTPException) as context:
            TransactionValidators.validate_receiver_action_allowed(mock_transaction, self.sender)

        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("Only the receiver can accept/decline", context.exception.detail)

    @patch.object(TransactionValidators, 'validate_receiver_action_allowed')
    def test_validate_transaction_declinable_success(self, mock_validate_action):
        """Test successful transaction decline validation."""
        mock_transaction = self._create_mock_transaction()
        mock_validate_action.return_value = True

        result = TransactionValidators.validate_transaction_declinable(mock_transaction, self.receiver)

        self.assertTrue(result)
        mock_validate_action.assert_called_once_with(mock_transaction, self.receiver)

    @patch.object(TransactionValidators, 'validate_receiver_action_allowed')
    def test_validate_transaction_acceptable_success(self, mock_validate_action):
        """Test successful transaction acceptance validation."""
        mock_transaction = self._create_mock_transaction()
        mock_validate_action.return_value = True

        result = TransactionValidators.validate_transaction_acceptable(mock_transaction, self.receiver)

        self.assertTrue(result)
        mock_validate_action.assert_called_once_with(mock_transaction, self.receiver)

    def test_validate_transaction_declinable_integration(self):
        """Test transaction decline validation with real receiver action validation."""
        mock_transaction = self._create_mock_transaction(
            sender_id=1,
            receiver_id=2,
            status=TransactionStatus.AWAITING_ACCEPTANCE
        )

        result = TransactionValidators.validate_transaction_declinable(mock_transaction, self.receiver)
        self.assertTrue(result)

    def test_validate_transaction_acceptable_integration(self):
        """Test transaction acceptance validation with real receiver action validation."""
        mock_transaction = self._create_mock_transaction(
            sender_id=1,
            receiver_id=2,
            status=TransactionStatus.AWAITING_ACCEPTANCE
        )

        result = TransactionValidators.validate_transaction_acceptable(mock_transaction, self.receiver)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()