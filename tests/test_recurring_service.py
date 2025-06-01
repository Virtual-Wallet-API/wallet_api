"""
Unit tests for RecurringService business logic.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, date, timedelta
from fastapi import HTTPException
import sys

# Mock the scheduler module to avoid apscheduler dependency
with patch.dict('sys.modules', {'app.infrestructure.scheduler': Mock()}):
    from tests.base_test import BaseTestCase
    from app.business.transaction.transactions_recurring import RecurringService
    from app.models import Transaction, RecurringTransaction, RecurringTransactionHistory, User
    from app.models.recurring_transation import RecurringInterval
    from app.models.transaction import TransactionStatus


class TestRecurringService(BaseTestCase):
    """Test cases for RecurringService."""

    def setUp(self):
        super().setUp()
        self.sender = self._create_mock_user(user_id=1, balance=1000.0)
        self.receiver = self._create_mock_user(user_id=2, balance=500.0)

        # Add available_balance property for sender
        self.sender.available_balance = self.sender.balance

        # Create mock recurring transaction
        self.mock_recurring_transaction = Mock()
        self.mock_recurring_transaction.id = 1
        self.mock_recurring_transaction.interval = RecurringInterval.DAILY
        self.mock_recurring_transaction.is_active = True

        # Create mock transaction
        self.mock_transaction = self._create_mock_transaction(
            transaction_id=1,
            sender_id=self.sender.id,
            receiver_id=self.receiver.id,
            amount=100.0,
            status=TransactionStatus.ACCEPTED,
            recurring=True
        )
        self.mock_transaction.sender = self.sender
        self.mock_transaction.receiver = self.receiver
        self.mock_transaction.currency = Mock()
        self.mock_transaction.currency.name = "USD"

    def test_gen_recurring_transaction_map_no_previous_execution(self):
        """Test generating transaction map when no previous execution exists."""
        # Arrange
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = None  # No previous execution
        self.mock_db.query.return_value = query_mock

        # Act
        result = RecurringService.gen_recurring_transaction_map(
            self.mock_transaction, self.mock_db, 1, RecurringInterval.DAILY
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["rid"], 1)
        self.assertEqual(result["amount"], 100.0)
        self.assertEqual(result["sender"], self.sender)
        self.assertEqual(result["receiver"], self.receiver)

        # Verify database query was made
        self.mock_db.query.assert_called_once_with(RecurringTransactionHistory)

    def test_gen_recurring_transaction_map_daily_interval_should_execute(self):
        """Test daily interval should execute when last execution was yesterday."""
        # Arrange
        yesterday = date.today() - timedelta(days=1)
        mock_history = Mock()
        mock_history.execution_date.date.return_value = yesterday

        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = mock_history
        self.mock_db.query.return_value = query_mock

        # Act
        result = RecurringService.gen_recurring_transaction_map(
            self.mock_transaction, self.mock_db, 1, RecurringInterval.DAILY
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["rid"], 1)

    def test_gen_recurring_transaction_map_daily_interval_already_executed_today(self):
        """Test daily interval should not execute when already executed today."""
        # Arrange
        today = date.today()
        mock_history = Mock()
        mock_history.execution_date.date.return_value = today

        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = mock_history
        self.mock_db.query.return_value = query_mock

        # Act
        result = RecurringService.gen_recurring_transaction_map(
            self.mock_transaction, self.mock_db, 1, RecurringInterval.DAILY
        )

        # Assert
        self.assertIsNone(result)

    def test_gen_recurring_transaction_map_weekly_interval_should_execute(self):
        """Test weekly interval should execute when 7 days have passed."""
        # Arrange
        seven_days_ago = date.today() - timedelta(days=7)
        mock_history = Mock()
        mock_history.execution_date.date.return_value = seven_days_ago

        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = mock_history
        self.mock_db.query.return_value = query_mock

        # Act
        result = RecurringService.gen_recurring_transaction_map(
            self.mock_transaction, self.mock_db, 1, RecurringInterval.WEEKLY
        )

        # Assert
        self.assertIsNotNone(result)

    def test_gen_recurring_transaction_map_weekly_interval_should_not_execute(self):
        """Test weekly interval should not execute when less than 7 days have passed."""
        # Arrange
        three_days_ago = date.today() - timedelta(days=3)
        mock_history = Mock()
        mock_history.execution_date.date.return_value = three_days_ago

        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = mock_history
        self.mock_db.query.return_value = query_mock

        # Act
        result = RecurringService.gen_recurring_transaction_map(
            self.mock_transaction, self.mock_db, 1, RecurringInterval.WEEKLY
        )

        # Assert
        self.assertIsNone(result)

    def test_gen_recurring_transaction_map_monthly_interval_should_execute(self):
        """Test monthly interval should execute when 30 days have passed."""
        # Arrange
        thirty_days_ago = date.today() - timedelta(days=30)
        mock_history = Mock()
        mock_history.execution_date.date.return_value = thirty_days_ago

        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = mock_history
        self.mock_db.query.return_value = query_mock

        # Act
        result = RecurringService.gen_recurring_transaction_map(
            self.mock_transaction, self.mock_db, 1, RecurringInterval.MONTHLY
        )

        # Assert
        self.assertIsNotNone(result)

    def test_gen_recurring_transaction_map_monthly_interval_should_not_execute(self):
        """Test monthly interval should not execute when less than 30 days have passed."""
        # Arrange
        fifteen_days_ago = date.today() - timedelta(days=15)
        mock_history = Mock()
        mock_history.execution_date.date.return_value = fifteen_days_ago

        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = mock_history
        self.mock_db.query.return_value = query_mock

        # Act
        result = RecurringService.gen_recurring_transaction_map(
            self.mock_transaction, self.mock_db, 1, RecurringInterval.MONTHLY
        )

        # Assert
        self.assertIsNone(result)

    def test_transfer_balance_success(self):
        """Test successful balance transfer."""
        # Arrange
        initial_sender_balance = self.sender.balance
        initial_receiver_balance = self.receiver.balance
        transfer_amount = 100.0

        # Act
        result = RecurringService.transfer_balance(
            self.mock_db, self.sender, self.receiver, transfer_amount
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(self.sender.balance, initial_sender_balance - transfer_amount)
        self.assertEqual(self.receiver.balance, initial_receiver_balance + transfer_amount)
        self.mock_db.commit.assert_called_once()

    def test_transfer_balance_failure(self):
        """Test balance transfer failure with database exception."""
        # Arrange
        self.mock_db.commit.side_effect = Exception("Database error")

        # Act
        result = RecurringService.transfer_balance(
            self.mock_db, self.sender, self.receiver, 100.0
        )

        # Assert
        self.assertFalse(result)

    @patch('app.business.transaction.transactions_recurring.UserAuthService.verify_user_can_transact')
    @patch('app.business.transaction.transactions_recurring.NotificationService.notify_from_template')
    def test_attempt_execute_recurring_insufficient_balance(self, mock_notify, mock_verify_transact):
        """Test recurring execution fails with insufficient balance."""
        # Arrange
        self.sender.available_balance = 50.0  # Less than transaction amount
        transaction_map = [{
            "rid": 1,
            "amount": 100.0,
            "date": datetime.now(),
            "sender": self.sender,
            "receiver": self.receiver,
            "currency": self.mock_transaction.currency
        }]

        # Act
        result = RecurringService.attempt_execute_recurring(self.mock_db, transaction_map)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["failed"])
        self.assertEqual(result[0]["reason"], "Insufficient balance")
        mock_notify.assert_called_once()

    @patch('app.business.transaction.transactions_recurring.UserAuthService.verify_user_can_transact')
    def test_attempt_execute_recurring_sender_cannot_transact(self, mock_verify_transact):
        """Test recurring execution fails when sender cannot transact."""
        # Arrange
        mock_verify_transact.side_effect = [False, True]  # Sender cannot transact, receiver can
        transaction_map = [{
            "rid": 1,
            "amount": 100.0,
            "date": datetime.now(),
            "sender": self.sender,
            "receiver": self.receiver,
            "currency": self.mock_transaction.currency
        }]

        # Act
        result = RecurringService.attempt_execute_recurring(self.mock_db, transaction_map)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["failed"])
        self.assertEqual(result[0]["reason"], "Account has suspended rights to transact")

    @patch('app.business.transaction.transactions_recurring.UserAuthService.verify_user_can_transact')
    def test_attempt_execute_recurring_receiver_cannot_transact(self, mock_verify_transact):
        """Test recurring execution fails when receiver cannot transact."""
        # Arrange
        mock_verify_transact.side_effect = [True, False]  # Sender can transact, receiver cannot
        transaction_map = [{
            "rid": 1,
            "amount": 100.0,
            "date": datetime.now(),
            "sender": self.sender,
            "receiver": self.receiver,
            "currency": self.mock_transaction.currency
        }]

        # Act
        result = RecurringService.attempt_execute_recurring(self.mock_db, transaction_map)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["failed"])
        self.assertEqual(result[0]["reason"], "Account has suspended rights to transact")

    @patch('app.business.transaction.transactions_recurring.UserAuthService.verify_user_can_transact')
    @patch('app.business.transaction.transactions_recurring.RecurringService.transfer_balance')
    def test_attempt_execute_recurring_success(self, mock_transfer, mock_verify_transact):
        """Test successful recurring execution."""
        # Arrange
        mock_verify_transact.return_value = True  # Both users can transact
        mock_transfer.return_value = True  # Transfer succeeds
        transaction_map = [{
            "rid": 1,
            "amount": 100.0,
            "date": datetime.now(),
            "sender": self.sender,
            "receiver": self.receiver,
            "currency": self.mock_transaction.currency
        }]

        # Act
        result = RecurringService.attempt_execute_recurring(self.mock_db, transaction_map)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["failed"])
        self.assertEqual(result[0]["reason"], "")
        mock_transfer.assert_called_once_with(self.mock_db, self.sender, self.receiver, 100.0)

    @patch('app.business.transaction.transactions_recurring.UserAuthService.verify_user_can_transact')
    @patch('app.business.transaction.transactions_recurring.RecurringService.transfer_balance')
    def test_attempt_execute_recurring_transfer_failure(self, mock_transfer, mock_verify_transact):
        """Test recurring execution with transfer failure."""
        # Arrange
        mock_verify_transact.return_value = True
        mock_transfer.return_value = False  # Transfer fails
        transaction_map = [{
            "rid": 1,
            "amount": 100.0,
            "date": datetime.now(),
            "sender": self.sender,
            "receiver": self.receiver,
            "currency": self.mock_transaction.currency
        }]

        # Act
        result = RecurringService.attempt_execute_recurring(self.mock_db, transaction_map)

        # Assert
        self.assertEqual(len(result), 0)  # No results when transfer fails

    def test_log_recurring_attempts_mixed_results(self):
        """Test logging of mixed successful and failed attempts."""
        # Arrange
        attempts = [[
            {
                "failed": False,
                "reason": "",
                "map": {"rid": 1, "date": datetime.now()}
            },
            {
                "failed": True,
                "reason": "Insufficient balance",
                "map": {"rid": 2, "date": datetime.now()}
            }
        ]]

        # Act
        completed, failed = RecurringService.log_recurring_attempts(*attempts, db=self.mock_db)

        # Assert
        self.assertEqual(completed, 1)
        self.assertEqual(failed, 1)
        self.assertEqual(self.mock_db.add.call_count, 2)
        self.assertEqual(self.mock_db.commit.call_count, 2)

    def test_log_recurring_attempts_all_successful(self):
        """Test logging of all successful attempts."""
        # Arrange
        attempts = [[
            {
                "failed": False,
                "reason": "",
                "map": {"rid": 1, "date": datetime.now()}
            },
            {
                "failed": False,
                "reason": "",
                "map": {"rid": 2, "date": datetime.now()}
            }
        ]]

        # Act
        completed, failed = RecurringService.log_recurring_attempts(*attempts, db=self.mock_db)

        # Assert
        self.assertEqual(completed, 2)
        self.assertEqual(failed, 0)

    def test_log_recurring_attempts_all_failed(self):
        """Test logging of all failed attempts."""
        # Arrange
        attempts = [[
            {
                "failed": True,
                "reason": "Insufficient balance",
                "map": {"rid": 1, "date": datetime.now()}
            },
            {
                "failed": True,
                "reason": "Account suspended",
                "map": {"rid": 2, "date": datetime.now()}
            }
        ]]

        # Act
        completed, failed = RecurringService.log_recurring_attempts(*attempts, db=self.mock_db)

        # Assert
        self.assertEqual(completed, 0)
        self.assertEqual(failed, 2)

    @patch('app.business.transaction.transactions_recurring.SessionLocal')
    @patch('app.business.transaction.transactions_recurring.RecurringService.gen_recurring_transaction_map')
    @patch('app.business.transaction.transactions_recurring.RecurringService.attempt_execute_recurring')
    @patch('app.business.transaction.transactions_recurring.RecurringService.log_recurring_attempts')
    def test_execute_recurring_transactions_success(self, mock_log, mock_attempt, mock_gen_map, mock_session):
        """Test successful execution of recurring transactions."""
        # Arrange
        current_date = datetime.now()
        mock_recurring = self._create_mock_recurring_transaction(
            recurring_id=1,
            next_execution=current_date - timedelta(days=1)  # Past due
        )

        # Create mock query object instead of list
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_recurring]

        with patch('app.business.transaction.transactions_recurring.db.query') as mock_db_query:
            mock_db_query.return_value = mock_query

            with patch.object(RecurringService, 'create_transaction_from_recurring') as mock_create:
                mock_create.return_value = Mock()

                # Act
                RecurringService.execute_recurring_transactions()

                # Assert
                mock_create.assert_called_once()

    @patch('app.business.transaction.transactions_recurring.SessionLocal')
    def test_execute_recurring_transactions_database_error(self, mock_session):
        """Test execution when database connection fails."""
        # Arrange
        mock_session.return_value.__enter__.return_value = None

        # Act
        with patch('builtins.print') as mock_print:
            RecurringService.execute_recurring_transactions()

        # Assert
        mock_print.assert_called_with("Database connection error, unable to execute recurring transactions.")

    @patch('app.business.transaction.transactions_recurring.schedule_daily_job')
    def test_register_recurring_transactions(self, mock_schedule):
        """Test registration of recurring transactions job."""
        # Act
        RecurringService.register_recurring_transactions()

        # Assert
        mock_schedule.assert_called_once_with(
            func=RecurringService.execute_recurring_transactions,
            hour=8,
            minute=0,
            job_id="execute_recurring_transactions"
        )

    def test_intervals_constant(self):
        """Test that INTERVALS constant contains expected values."""
        expected_intervals = [
            RecurringInterval.DAILY,
            RecurringInterval.WEEKLY,
            RecurringInterval.MONTHLY
        ]

        self.assertEqual(RecurringService.INTERVALS, expected_intervals)


if __name__ == '__main__':
    unittest.main() 