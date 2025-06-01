"""
Unit tests for UserValidators business logic.
"""
import unittest
from unittest.mock import Mock
from fastapi import HTTPException

from tests.base_test import BaseTestCase
from app.business.user.user_validators import UserValidators
from app.models import User


class TestUserValidators(BaseTestCase):
    """Test cases for UserValidators."""

    def setUp(self):
        super().setUp()
        self.user_id = 1
        self.username = "testuser"
        self.email = "test@example.com"
        self.phone_number = "1234567890"

        # Create mock user
        self.mock_user = self._create_mock_user(
            user_id=self.user_id,
            username=self.username,
            email=self.email,
            phone_number=self.phone_number
        )

    def test_search_user_by_identifier_by_id(self):
        """Test successful user search by ID."""
        query_mock = self.setup_db_query_mock(User, self.mock_user)
        query_mock.first.return_value = self.mock_user

        result = UserValidators.search_user_by_identifier(self.mock_db, self.user_id)

        self.assertEqual(result, self.mock_user)
        self.mock_db.query.assert_called_with(User)

    def test_search_user_by_identifier_by_username(self):
        """Test successful user search by username."""
        # Mock that ID search fails, username succeeds
        query_mock = self.setup_db_query_mock(User, [])

        # First call (ID) returns None, second call (username) returns user
        query_mock.first.side_effect = [None, self.mock_user]

        result = UserValidators.search_user_by_identifier(self.mock_db, self.username)

        self.assertEqual(result, self.mock_user)

    def test_search_user_by_identifier_by_email(self):
        """Test successful user search by email."""
        # Mock that ID and username searches fail, email succeeds
        query_mock = self.setup_db_query_mock(User, [])
        query_mock.first.side_effect = [None, None, self.mock_user]

        result = UserValidators.search_user_by_identifier(self.mock_db, self.email)

        self.assertEqual(result, self.mock_user)

    def test_search_user_by_identifier_by_phone(self):
        """Test successful user search by phone number."""
        # Mock that first three searches fail, phone succeeds
        query_mock = self.setup_db_query_mock(User, [])
        query_mock.first.side_effect = [None, None, None, self.mock_user]

        result = UserValidators.search_user_by_identifier(self.mock_db, self.phone_number)

        self.assertEqual(result, self.mock_user)

    def test_search_user_by_identifier_not_found(self):
        """Test user search fails when user not found by any identifier."""
        # Mock all searches to return None
        query_mock = self.setup_db_query_mock(User, [])
        query_mock.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            UserValidators.search_user_by_identifier(self.mock_db, "nonexistent")

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("does not exist", context.exception.detail)

    def test_find_user_with_success(self):
        """Test successful user finding with specific field."""
        query_mock = self.setup_db_query_mock(User, self.mock_user)
        query_mock.first.return_value = self.mock_user

        result = UserValidators.find_user_with("username", self.username, self.mock_db)

        self.assertEqual(result, self.mock_user)
        self.mock_db.query.assert_called_with(User)

    def test_find_user_with_not_found(self):
        """Test user finding returns False when user not found."""
        query_mock = self.setup_db_query_mock(User, [])
        query_mock.first.return_value = None

        result = UserValidators.find_user_with("username", "nonexistent", self.mock_db)

        self.assertFalse(result)

    def test_find_user_with_all_valid_fields(self):
        """Test finding user with all valid field types."""
        query_mock = self.setup_db_query_mock(User, self.mock_user)
        query_mock.first.return_value = self.mock_user

        # Test all valid fields
        fields_to_test = [
            ("id", self.user_id),
            ("username", self.username),
            ("email", self.email),
            ("phone", self.phone_number)
        ]

        for field, value in fields_to_test:
            with self.subTest(field=field):
                self.mock_db.reset_mock()
                query_mock = self.setup_db_query_mock(User, self.mock_user)
                query_mock.first.return_value = self.mock_user

                result = UserValidators.find_user_with(field, value, self.mock_db)
                self.assertEqual(result, self.mock_user)

    def test_find_user_with_or_raise_exception_success(self):
        """Test successful user finding with exception raising version."""
        query_mock = self.setup_db_query_mock(User, self.mock_user)
        query_mock.first.return_value = self.mock_user

        result = UserValidators.find_user_with_or_raise_exception("username", self.username, self.mock_db)

        self.assertEqual(result, self.mock_user)

    def test_find_user_with_or_raise_exception_not_found_default(self):
        """Test exception raising when user not found with default exception."""
        query_mock = self.setup_db_query_mock(User, [])
        query_mock.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            UserValidators.find_user_with_or_raise_exception("username", "nonexistent", self.mock_db)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("does not exist", context.exception.detail)

    def test_find_user_with_or_raise_exception_custom_exception(self):
        """Test exception raising when user not found with custom exception."""
        query_mock = self.setup_db_query_mock(User, [])
        query_mock.first.return_value = None

        custom_exception = HTTPException(status_code=404, detail="Custom error message")

        with self.assertRaises(HTTPException) as context:
            UserValidators.find_user_with_or_raise_exception(
                "username", "nonexistent", self.mock_db, custom_exception
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("Custom error message", context.exception.detail)

    def test_find_user_with_or_raise_exception_invalid_field(self):
        """Test exception raising when invalid field is provided."""
        with self.assertRaises(ValueError) as context:
            UserValidators.find_user_with_or_raise_exception("invalid_field", "value", self.mock_db)

        self.assertIn("Invalid field", str(context.exception))
        self.assertIn("invalid_field", str(context.exception))

    def test_validate_unique_user_data_username_taken(self):
        """Test unique user data validation when username is taken."""
        query_mock = self.setup_db_query_mock(User, self.mock_user)
        query_mock.first.return_value = self.mock_user

        user_data = {"username": self.username, "email": "new@example.com"}
        result = UserValidators.validate_unique_user_data(user_data, self.mock_db)

        self.assertEqual(result, self.mock_user)

    def test_validate_unique_user_data_email_taken(self):
        """Test unique user data validation when email is taken."""
        query_mock = self.setup_db_query_mock(User, [])
        # First call (username) returns None, second call (email) returns user
        query_mock.first.side_effect = [None, self.mock_user]

        user_data = {"username": "newuser", "email": self.email}
        result = UserValidators.validate_unique_user_data(user_data, self.mock_db)

        self.assertEqual(result, self.mock_user)

    def test_validate_unique_user_data_phone_taken(self):
        """Test unique user data validation when phone is taken."""
        query_mock = self.setup_db_query_mock(User, [])
        # First two calls return None, third call (phone) returns user
        query_mock.first.side_effect = [None, None, self.mock_user]

        user_data = {"username": "newuser", "email": "new@example.com", "phone": self.phone_number}
        result = UserValidators.validate_unique_user_data(user_data, self.mock_db)

        self.assertEqual(result, self.mock_user)

    def test_validate_unique_user_data_all_unique(self):
        """Test unique user data validation when all data is unique."""
        query_mock = self.setup_db_query_mock(User, [])
        query_mock.first.return_value = None

        user_data = {"username": "newuser", "email": "new@example.com", "phone": "9999999999"}
        result = UserValidators.validate_unique_user_data(user_data, self.mock_db)

        self.assertFalse(result)

    def test_validate_unique_user_data_ignores_non_unique_fields(self):
        """Test that unique validation ignores non-unique fields."""
        query_mock = self.setup_db_query_mock(User, [])
        query_mock.first.return_value = None

        user_data = {
            "username": "newuser",
            "password": "somepassword",  # Should be ignored
            "first_name": "John",  # Should be ignored
            "last_name": "Doe"  # Should be ignored
        }
        result = UserValidators.validate_unique_user_data(user_data, self.mock_db)

        self.assertFalse(result)
        # Should only check username (1 call), not password, first_name, last_name
        self.assertEqual(query_mock.first.call_count, 1)

    def test_validate_unique_user_data_empty_data(self):
        """Test unique user data validation with empty data."""
        result = UserValidators.validate_unique_user_data({}, self.mock_db)

        self.assertFalse(result)
        # Should not make any database calls
        self.mock_db.query.assert_not_called()

    def test_unique_validation_tuple_coverage(self):
        """Test that UniqueValidation tuple contains expected fields."""
        expected_fields = ("username", "email", "phone")
        self.assertEqual(UserValidators.UniqueValidation, expected_fields)

    def test_find_user_with_or_raise_exception_all_fields(self):
        """Test find_user_with_or_raise_exception with all valid fields."""
        query_mock = self.setup_db_query_mock(User, self.mock_user)
        query_mock.first.return_value = self.mock_user

        # Test all valid fields
        fields_to_test = [
            ("id", self.user_id),
            ("username", self.username),
            ("email", self.email),
            ("phone", self.phone_number)
        ]

        for field, value in fields_to_test:
            with self.subTest(field=field):
                self.mock_db.reset_mock()
                query_mock = self.setup_db_query_mock(User, self.mock_user)
                query_mock.first.return_value = self.mock_user

                result = UserValidators.find_user_with_or_raise_exception(field, value, self.mock_db)
                self.assertEqual(result, self.mock_user)


if __name__ == '__main__':
    unittest.main()