"""
Unit tests for AdminService business logic.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from tests.base_test import BaseTestCase
from app.business.user.user_admin import AdminService
from app.models import User, Transaction
from app.models.user import UserStatus as UStatus
from app.schemas.admin import UpdateUserStatus, AdminUserResponse
from app.schemas.router import AdminUserFilter


class TestAdminService(BaseTestCase):
    """Test cases for AdminService."""

    def setUp(self):
        super().setUp()
        self.pending_user = self._create_mock_user(user_id=2, status=UStatus.PENDING)
        self.blocked_user = self._create_mock_user(user_id=3, status=UStatus.BLOCKED)
        self.pending_user.cards = [self._create_mock_card()]  # User has a card

    def test_verify_admin_with_admin_user(self):
        """Test admin verification with valid admin user."""
        # Act
        result = AdminService.verify_admin(self.mock_db, self.mock_admin)

        # Assert
        self.assertTrue(result)

    def test_verify_admin_with_non_admin_user(self):
        """Test admin verification with non-admin user raises exception."""
        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            AdminService.verify_admin(self.mock_db, self.mock_user)

        self.assertEqual(context.exception.status_code, 403)
        self.assertIn("permission", context.exception.detail)

    @patch('app.business.user.user_validators.UserValidators.find_user_with_or_raise_exception')
    def test_verify_admin_with_username_string(self, mock_find_user):
        """Test admin verification with username string."""
        # Arrange
        mock_find_user.return_value = self.mock_admin

        # Act
        result = AdminService.verify_admin(self.mock_db, 'admin_username')

        # Assert
        mock_find_user.assert_called_once_with("username", "admin_username", self.mock_db)
        self.assertTrue(result)

    @patch('app.business.user.user_validators.UserValidators.search_user_by_identifier')
    @patch('app.business.utils.notification_service.NotificationService.notify_from_template')
    def test_update_user_status_approve_pending_user(self, mock_notify, mock_search_user):
        """Test successful approval of pending user to active status."""
        # Arrange
        mock_search_user.return_value = self.pending_user
        update_data = UpdateUserStatus(status=UStatus.ACTIVE.value)

        # Act
        result = AdminService.update_user_status(self.mock_db, 2, update_data, self.mock_admin)

        # Assert
        mock_search_user.assert_called_once_with(self.mock_db, 2)
        self.assertEqual(self.pending_user.status, UStatus.ACTIVE)
        self.assert_db_operations_called(add=False, commit=True, refresh=True)
        mock_notify.assert_called_once()
        self.assertIn("approved successfully", result["message"])

    @patch('app.business.user.user_validators.UserValidators.search_user_by_identifier')
    def test_update_user_status_approve_pending_user_without_card(self, mock_search_user):
        """Test approval fails for pending user without cards."""
        # Arrange
        user_without_cards = self._create_mock_user(user_id=2, status=UStatus.PENDING)
        user_without_cards.cards = []  # No cards
        mock_search_user.return_value = user_without_cards
        update_data = UpdateUserStatus(status=UStatus.ACTIVE.value)

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            AdminService.update_user_status(self.mock_db, 2, update_data, self.mock_admin)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("must have a debit or credit card", context.exception.detail)

    @patch('app.business.user.user_validators.UserValidators.search_user_by_identifier')
    @patch('app.business.utils.notification_service.NotificationService.notify_from_template')
    def test_update_user_status_block_user(self, mock_notify, mock_search_user):
        """Test successful blocking of user."""
        # Arrange
        mock_search_user.return_value = self.mock_user
        update_data = UpdateUserStatus(status=UStatus.BLOCKED.value)

        # Act
        result = AdminService.update_user_status(self.mock_db, 1, update_data, self.mock_admin)

        # Assert
        self.assertEqual(self.mock_user.status, UStatus.BLOCKED)
        self.assert_db_operations_called(add=False, commit=True, refresh=True)
        mock_notify.assert_called_once()
        self.assertIn("blocked successfully", result["message"])

    @patch('app.business.user.user_validators.UserValidators.search_user_by_identifier')
    def test_update_user_status_block_already_blocked_user(self, mock_search_user):
        """Test blocking already blocked user returns appropriate message."""
        # Arrange
        mock_search_user.return_value = self.blocked_user
        update_data = UpdateUserStatus(status=UStatus.BLOCKED.value)

        # Act
        result = AdminService.update_user_status(self.mock_db, 3, update_data, self.mock_admin)

        # Assert
        self.assertIn("already blocked", result["message"])

    @patch('app.business.user.user_validators.UserValidators.search_user_by_identifier')
    @patch('app.business.utils.notification_service.NotificationService.notify_from_template')
    def test_update_user_status_deactivate_user(self, mock_notify, mock_search_user):
        """Test successful deactivation of user."""
        # Arrange
        mock_search_user.return_value = self.mock_user
        update_data = UpdateUserStatus(status=UStatus.DEACTIVATED.value)

        # Act
        result = AdminService.update_user_status(self.mock_db, 1, update_data, self.mock_admin)

        # Assert
        self.assertEqual(self.mock_user.status, UStatus.DEACTIVATED)
        self.assert_db_operations_called(add=False, commit=True, refresh=True)
        mock_notify.assert_called_once()
        self.assertIn("deactivated successfully", result["message"])

    def test_update_user_status_invalid_status(self):
        """Test update_user_status with invalid status."""
        # Arrange & Act & Assert
        with self.assertRaises(ValueError):  # Pydantic validation error becomes ValueError in test
            update_data = UpdateUserStatus(status="INVALID_STATUS")

    def test_update_user_status_with_user_object(self):
        """Test update user status when User object is passed directly."""
        # Arrange
        update_data = UpdateUserStatus(status=UStatus.ACTIVE.value)
        self.pending_user.cards = [self._create_mock_card()]  # Ensure user has cards

        # Act
        with patch('app.business.utils.notification_service.NotificationService.notify_from_template'):
            result = AdminService.update_user_status(self.mock_db, self.pending_user, update_data, self.mock_admin)

        # Assert
        self.assertEqual(self.pending_user.status, UStatus.ACTIVE)
        self.assertIn("approved successfully", result["message"])

    def test_get_all_users_without_search(self):
        """Test get_all_users without search parameters."""
        # Arrange
        search_filter = AdminUserFilter(page=1, limit=10)

        # Create a list of mock users that can be iterated
        mock_users = [
            self._create_mock_user_with_transactions_count(user_id=1, username="user1", transactions_count=5),
            self._create_mock_user_with_transactions_count(user_id=2, username="user2", transactions_count=3)
        ]

        # Set up query mock
        mock_query = Mock()
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_users  # Return the iterable list
        self.mock_db.query.return_value = mock_query

        # Act
        result = AdminService.get_all_users(self.mock_db, self.mock_admin, search_filter)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result["results_per_page"], 10)
        self.assertEqual(len(result["users"]), 2)
        self.assertEqual(result["matching_records"], 2)

    def test_get_all_users_with_username_search(self):
        """Test get_all_users with username search."""
        # Arrange
        search_filter = AdminUserFilter(page=1, limit=10, search_by="username", search_query="test")

        # Create a list of mock users that can be iterated
        mock_users = [
            self._create_mock_user_with_transactions_count(user_id=1, username="testuser", transactions_count=2)
        ]

        # Set up query mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_users  # Return the iterable list
        self.mock_db.query.return_value = mock_query

        # Act
        result = AdminService.get_all_users(self.mock_db, self.mock_admin, search_filter)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result["users"]), 1)
        self.assertEqual(result["matching_records"], 1)

    def test_get_all_users_with_email_search(self):
        """Test get_all_users with email search."""
        # Arrange
        search_filter = AdminUserFilter(page=1, limit=10, search_by="email", search_query="test@")

        # Create a list of mock users that can be iterated
        mock_users = [
            self._create_mock_user_with_transactions_count(user_id=1, email="test@example.com", transactions_count=4)
        ]

        # Set up query mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_users  # Return the iterable list
        self.mock_db.query.return_value = mock_query

        # Act
        result = AdminService.get_all_users(self.mock_db, self.mock_admin, search_filter)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result["users"]), 1)
        self.assertEqual(result["matching_records"], 1)

    def test_get_all_users_with_phone_search(self):
        """Test get_all_users with phone search."""
        # Arrange
        search_filter = AdminUserFilter(page=1, limit=10, search_by="phone", search_query="123")

        # Create a list of mock users that can be iterated
        mock_users = [
            self._create_mock_user_with_transactions_count(user_id=1, phone_number="1234567890", transactions_count=1)
        ]

        # Set up query mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_users  # Return the iterable list
        self.mock_db.query.return_value = mock_query

        # Act
        result = AdminService.get_all_users(self.mock_db, self.mock_admin, search_filter)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result["users"]), 1)
        self.assertEqual(result["matching_records"], 1)

    def test_get_all_users_with_invalid_search_by(self):
        """Test get_all_users with invalid search_by parameter."""
        # Arrange & Act & Assert
        with self.assertRaises(ValueError):  # Pydantic validation error becomes ValueError in test
            search_filter = AdminUserFilter(
                search_by="invalid_field",
                search_value="test",
                limit=10,
                offset=0
            )

    def test_get_all_users_no_results(self):
        """Test getting users when no results found."""
        # Arrange
        query_mock = MagicMock()
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        self.mock_db.query.return_value = query_mock

        search_filter = AdminUserFilter(
            search_by=None,
            search_query=None,
            page=1,
            limit=10
        )

        # Act
        result = AdminService.get_all_users(self.mock_db, self.mock_admin, search_filter)

        # Assert
        self.assertEqual(result["users"], [])
        self.assertEqual(result["page"], 0)
        self.assertEqual(result["pages_with_matches"], 0)
        self.assertEqual(result["matching_records"], 0)

    @patch('app.business.user.user_admin.UVal.find_user_with_or_raise_exception')
    def test_get_user_transactions_success(self, mock_find_user):
        """Test successful retrieval of user transactions."""
        # Mock the user object with get_transactions method
        mock_user = Mock()
        mock_transaction = self._create_mock_admin_transaction()
        mock_query = Mock()
        mock_query.all.return_value = [mock_transaction]
        mock_user.get_transactions.return_value = mock_query
        mock_find_user.return_value = mock_user

        # Use Dict instead of AdminTransactionSearch
        search_data = {
            "user_id": 1,
            "page": 1,
            "limit": 10,
            "order_by": "date_desc"
        }

        # Act
        result = AdminService.get_user_transactions(self.mock_db, self.mock_admin, search_data)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn("transactions", result)
        self.assertEqual(result["results_per_page"], 10)
        mock_find_user.assert_called_once_with("id", 1, self.mock_db)

    @patch('app.business.user.user_validators.UserValidators.search_user_by_identifier')
    @patch('app.business.transaction.transaction_validators.TransactionValidators.validate_transaction_ownership')
    def test_deny_pending_transaction_success(self, mock_validate_ownership, mock_validate_user):
        """Test successful denial of pending transaction."""
        from app.models.transaction import TransactionStatus

        # Arrange
        mock_transaction = Mock()
        mock_transaction.id = 1
        mock_transaction.status = TransactionStatus.PENDING  # Use proper enum
        mock_transaction.cancel_transaction = Mock()
        mock_transaction.deny_transaction = Mock()

        mock_validate_user.return_value = self.mock_user
        mock_validate_ownership.return_value = mock_transaction

        # Mock the query to return our transaction
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_transaction
        self.mock_db.query.return_value = mock_query

        # Act
        result = AdminService.deny_pending_transaction(self.mock_db, 1, self.mock_admin)

        # Assert
        self.assertIsNotNone(result)
        mock_transaction.deny_transaction.assert_called_once()

    @patch('app.business.user.user_validators.UserValidators.search_user_by_identifier')
    def test_promote_user_to_admin_success(self, mock_validate):
        """Test successful user promotion to admin."""
        # Arrange
        regular_user = self._create_mock_user(user_id=2, is_admin=False)
        mock_validate.return_value = regular_user

        # Act
        result = AdminService.promote_user_to_admin(self.mock_db, 2, self.mock_admin)

        # Assert
        self.assertTrue(regular_user.is_admin)
        self.mock_db.commit.assert_called_once()
        mock_validate.assert_called_once_with(self.mock_db, 2)

    @patch('app.business.user.user_validators.UserValidators.search_user_by_identifier')
    def test_promote_user_to_admin_already_admin(self, mock_validate):
        """Test promotion of user who is already admin."""
        # Arrange
        mock_validate.return_value = self.mock_admin

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            AdminService.promote_user_to_admin(self.mock_db, 999, self.mock_admin)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("already an admin", context.exception.detail)

    @patch('app.business.user.user_validators.UserValidators.find_user_with_or_raise_exception')
    def test_block_user_success(self, mock_validate):
        """Test successful blocking of user by admin."""
        # Arrange
        mock_validate.return_value = self.mock_user

        # Act
        result = AdminService.block(self.mock_db, "testuser", "Violation of terms", self.mock_admin)

        # Assert
        self.mock_db.refresh.assert_called_once_with(self.mock_user)
        self.assertEqual(result, self.mock_user)

    def test_block_user_with_user_object(self):
        """Test blocking user when User object is passed directly."""
        # Act
        result = AdminService.block(self.mock_db, self.mock_user, "Violation of terms", self.mock_admin)

        # Assert
        self.mock_db.refresh.assert_called_once_with(self.mock_user)
        self.assertEqual(result, self.mock_user)


if __name__ == '__main__':
    unittest.main() 