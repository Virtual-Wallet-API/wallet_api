"""
Base test class with common utilities and mocks for all test cases.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict
from datetime import datetime

from sqlalchemy.orm import Session
from app.models import User, Transaction, Card, Category, Contact
from app.models.user import UserStatus as UStatus


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and utilities."""
    
    def setUp(self):
        """Set up common test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = self._create_mock_user()
        self.mock_admin = self._create_mock_admin()
        
    def tearDown(self):
        """Clean up after each test."""
        pass
    
    def _create_mock_user(self, user_id=1, username="testuser", email="test@example.com",
                          phone_number="1234567890", balance=100.0, status="active", is_admin=False):
        """Create a mock user with proper attributes."""
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.username = username
        mock_user.email = email
        mock_user.phone_number = str(phone_number)  # Ensure phone_number is always a string
        mock_user.balance = balance
        mock_user.status = status
        mock_user.is_admin = is_admin
        mock_user.admin = is_admin  # Some services use .admin instead of .is_admin
        mock_user.hashed_password = "hashedpassword123"

        # Add additional attributes that might be needed
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.avatar = "default_avatar.png"
        mock_user.cards_count = 2
        mock_user.contacts_count = 5
        mock_user.deposits_count = 10
        mock_user.withdrawals_count = 3

        # Add limit-related attributes for pending user verification
        mock_user.deactivated_cards = []  # Default to empty
        mock_user.active_cards = [Mock(), Mock()]  # Default to 2 cards
        mock_user.completed_deposits_count = 2  # Default within limits
        mock_user.cards = mock_user.active_cards  # Some services use .cards

        # Fix: Add proper list collections that services iterate over
        mock_user.withdrawals = []  # Default empty list for withdrawal iterations
        mock_user.deposits = []  # Default empty list for deposit iterations
        mock_user.completed_withdrawals = []
        mock_user.pending_withdrawals = []
        mock_user.failed_withdrawals = []
        mock_user.refunds = []
        mock_user.payouts = []
        mock_user.completed_deposits = []
        mock_user.pending_deposits = []
        mock_user.failed_deposits = []

        # Add available_balance property for transaction services
        mock_user.available_balance = balance

        return mock_user

    def _create_mock_admin(self):
        """Create a mock admin user."""
        return self._create_mock_user(
            user_id=999,
            username="admin",
            email="admin@example.com",
            is_admin=True,
            status="active"
        )

    def _create_mock_transaction(self, transaction_id: int = 1, **kwargs) -> Mock:
        """Create a mock transaction with default values."""
        default_attrs = {
            'id': transaction_id,
            'sender_id': 1,
            'receiver_id': 2,
            'amount': 100.0,
            'description': 'Test transaction',
            'status': 'COMPLETED',
            'category_id': 1,  # Fixed: Use integer instead of Mock
            'currency_id': 1,  # Fixed: Use integer instead of Mock
            'date': datetime.now(),  # Fixed: Use actual datetime instead of Mock
            'created_at': datetime.now(),
            'sender': self._create_mock_user(1),
            'receiver': self._create_mock_user(2)
        }
        default_attrs.update(kwargs)

        mock_transaction = Mock(spec=Transaction)
        for attr, value in default_attrs.items():
            setattr(mock_transaction, attr, value)

        return mock_transaction

    def _create_mock_card(self, card_id: int = 1, **kwargs) -> Mock:
        """Create a mock card with default values."""
        default_attrs = {
            'id': card_id,
            'user_id': 1,
            'card_number': '1234567812345678',
            'card_holder': 'Test User',
            'expiration_date': '12/25',
            'cvv': '123',
            'is_active': True
        }
        default_attrs.update(kwargs)

        mock_card = Mock(spec=Card)
        for attr, value in default_attrs.items():
            setattr(mock_card, attr, value)

        return mock_card

    def _create_mock_category(self, category_id: int = 1, **kwargs):
        """Create a mock category with default values."""
        default_attrs = {
            'id': category_id,
            'name': f'TestCategory{category_id}',
            'description': 'Test category description',
            'user_id': 1,
            'total_income': 0.0,
            'total_expense': 0.0,
            'total_transactions': 0,
            'completed_transactions': 0,
            'total_amount': 0.0,
            'transactions': []  # Important: empty list by default
        }
        default_attrs.update(kwargs)

        mock_category = Mock(spec=Category)
        for attr, value in default_attrs.items():
            setattr(mock_category, attr, value)

        return mock_category

    def _create_mock_contact(self, contact_id: int = 1, **kwargs) -> Mock:
        """Create a mock contact with default values."""
        default_attrs = {
            'id': contact_id,
            'user_id': 1,
            'contact_user_id': 2,
            'contact_user': self._create_mock_user(2)
        }
        default_attrs.update(kwargs)

        mock_contact = Mock(spec=Contact)
        for attr, value in default_attrs.items():
            setattr(mock_contact, attr, value)

        return mock_contact

    def _create_mock_withdrawal(self, withdrawal_id: int = 1, **kwargs) -> Mock:
        """Create a mock withdrawal with proper data types for Pydantic validation."""
        from app.models import WStatus, WType, WMethod

        default_attrs = {
            'id': withdrawal_id,
            'user_id': 1,
            'card_id': 1,
            'amount': 100.0,
            'amount_cents': 10000,  # Integer for Pydantic validation
            'status': WStatus.PENDING,
            'withdrawal_type': WType.PAYOUT,  # Fixed: Proper field name with enum value
            'method': WMethod.CARD,  # Fixed: Use CARD instead of STRIPE
            'description': 'Test withdrawal',
            'failure_reason': None,
            'estimated_arrival': '2-3 business days',
            'stripe_payout_id': 'po_test123',
            'stripe_refund_id': None,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'completed_at': None,
            'failed_at': None,
            # Card relationship
            'card': self._create_mock_card_for_withdrawal()
        }
        default_attrs.update(kwargs)

        mock_withdrawal = Mock()
        for attr, value in default_attrs.items():
            setattr(mock_withdrawal, attr, value)

        return mock_withdrawal

    def _create_mock_card_for_withdrawal(self, **kwargs) -> Mock:
        """Create a mock card specifically for withdrawal responses with proper data types."""
        default_attrs = {
            'id': 1,
            'last_four': '1234',
            'brand': 'visa',
            'exp_month': 12,
            'exp_year': 2025,
            'cardholder_name': 'Test User',
            'type': 'debit',  # Fixed: Use string instead of CardType enum
            'design': 'default',
            'is_default': True,
            'is_active': True,
            'masked_number': '**** **** **** 1234',
            'is_expired': False
        }
        default_attrs.update(kwargs)

        mock_card = Mock()
        for attr, value in default_attrs.items():
            setattr(mock_card, attr, value)

        return mock_card

    def _create_mock_deposit(self, deposit_id: int = 1, **kwargs) -> Mock:
        """Create a mock deposit with proper data types for Pydantic validation."""
        from app.models import DepositType, DepositMethod

        default_attrs = {
            'id': deposit_id,
            'user_id': 1,
            'card_id': 1,
            'amount': 100.0,
            'amount_cents': 10000,  # Added for Pydantic validation
            'deposit_type': DepositType.CARD_PAYMENT,
            'method': DepositMethod.STRIPE,
            'description': 'Test deposit',  # String instead of Mock
            'failure_reason': None,  # Can be None or string
            'stripe_charge_id': 'ch_test123',  # String instead of Mock
            'status': 'completed',
            'completed_at': datetime.now(),  # Proper datetime
            'created_at': datetime.now(),
            'updated_at': datetime.now(),  # Added missing field
            'failed_at': None,  # Can be None or datetime
            # Card relationship
            'card': self._create_mock_card_for_withdrawal()
        }
        default_attrs.update(kwargs)

        mock_deposit = Mock()
        for attr, value in default_attrs.items():
            setattr(mock_deposit, attr, value)

        return mock_deposit

    def _create_mock_user_with_transactions_count(self, user_id=1, transactions_count=5, **kwargs):
        """Create a mock user with proper transactions_count for admin responses."""
        mock_user = self._create_mock_user(user_id=user_id, **kwargs)
        mock_user.transactions_count = transactions_count  # Integer for Pydantic validation
        return mock_user

    def _create_mock_admin_transaction(self, transaction_id=1, **kwargs):
        """Create a mock transaction for admin responses with proper enum values."""
        from app.models.transaction import TransactionStatus

        default_attrs = {
            'id': transaction_id,
            'sender_id': 1,
            'receiver_id': 2,
            'amount': 100.0,
            'description': 'Test transaction',
            'status': TransactionStatus.COMPLETED.value,  # Use enum value instead of string
            'category_id': 1,
            'currency_id': 1,
            'date': datetime.now(),
            'created_at': datetime.now()
        }
        default_attrs.update(kwargs)

        mock_transaction = Mock()
        for attr, value in default_attrs.items():
            setattr(mock_transaction, attr, value)

        return mock_transaction

    def _create_mock_recurring_transaction(self, recurring_id=1, **kwargs):
        """Create a mock recurring transaction with proper data types."""
        from app.models.recurring_transation import RecurringInterval
        from app.models.transaction import TransactionStatus

        default_attrs = {
            'id': recurring_id,
            'sender_id': 1,
            'receiver_id': 2,
            'amount': 100.0,
            'description': 'Recurring payment',
            'interval': RecurringInterval.MONTHLY,
            'next_execution': datetime.now(),
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        default_attrs.update(kwargs)

        mock_recurring = Mock()
        for attr, value in default_attrs.items():
            setattr(mock_recurring, attr, value)

        return mock_recurring

    def setup_db_query_mock(self, model_class, return_value):
        """Set up a database query mock with the specified return value."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.options.return_value = query_mock
        query_mock.distinct.return_value = query_mock
        query_mock.all.return_value = return_value if isinstance(return_value, list) else [return_value]
        query_mock.first.return_value = return_value if not isinstance(return_value, list) else (return_value[0] if return_value else None)
        query_mock.count.return_value = len(return_value) if isinstance(return_value, list) else 1

        self.mock_db.query.return_value = query_mock
        return query_mock

    def assert_db_add_called_with_type(self, expected_type):
        """Assert that db.add was called with an instance of expected_type."""
        self.mock_db.add.assert_called()
        added_instance = self.mock_db.add.call_args[0][0]
        self.assertIsInstance(added_instance, expected_type)
        return added_instance

    def assert_db_operations_called(self, add=True, commit=True, refresh=False):
        """Assert that expected database operations were called."""
        if add:
            self.mock_db.add.assert_called()
        if commit:
            self.mock_db.commit.assert_called()
        if refresh:
            self.mock_db.refresh.assert_called()

    @patch('app.business.transaction.transaction_notifications.TransactionNotifications')
    def setup_notification_mocks(self, mock_notifications):
        """Set up notification service mocks."""
        self.mock_notifications = mock_notifications.return_value

        # Mock all notification methods
        self.mock_notifications.notify_sender_transaction_sent = Mock()
        self.mock_notifications.notify_receiver_transaction_received = Mock()
        self.mock_notifications.notify_sender_transaction_failed = Mock()
        self.mock_notifications.notify_sender_transaction_cancelled = Mock()
        self.mock_notifications.notify_sender_transaction_declined = Mock()
        self.mock_notifications.notify_sender_transaction_completed = Mock()
        self.mock_notifications.notify_receiver_transaction_completed = Mock()

        return self.mock_notifications


class MockDBSession:
    """Mock database session context manager."""
    
    def __init__(self, mock_session):
        self.mock_session = mock_session
    
    def __enter__(self):
        return self.mock_session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Common test decorators
def mock_db_session(func):
    """Decorator to mock database session for test methods."""
    def wrapper(self, *args, **kwargs):
        with patch('app.dependencies.get_db') as mock_get_db:
            mock_get_db.return_value = self.mock_db
            return func(self, *args, **kwargs)
    return wrapper


def mock_auth_dependencies(func):
    """Decorator to mock authentication dependencies."""
    def wrapper(self, *args, **kwargs):
        with patch('app.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = self.mock_user
            return func(self, *args, **kwargs)
    return wrapper 