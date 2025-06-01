"""
Unit tests for UserContacts business logic.
"""
import unittest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from tests.base_test import BaseTestCase
from app.business.user.user_contacts import UserContacts
from app.models import User, Contact
from app.schemas.contact import ContactCreate


class TestUserContacts(BaseTestCase):
    """Test cases for UserContacts."""

    def setUp(self):
        super().setUp()
        # Create mock users
        self.user = self._create_mock_user(user_id=1, username="testuser")
        self.contact_user = self._create_mock_user(user_id=2, username="contactuser")

        # Create mock contact
        self.mock_contact = Mock(spec=Contact)
        self.mock_contact.id = 1
        self.mock_contact.user_id = self.user.id
        self.mock_contact.contact_id = self.contact_user.id
        self.mock_contact.user = self.user
        self.mock_contact.contact_user = self.contact_user

        # Setup user.contacts relationship
        contacts_query = Mock()
        contacts_query.filter.return_value.first.return_value = self.mock_contact
        self.user.contacts = contacts_query

    def test_insert_contact_success(self):
        """Test successful contact insertion."""
        # Act
        result = UserContacts.insert_contact(self.mock_db, self.user, self.contact_user)

        # Assert
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_check_contact_exists_true(self):
        """Test check_contact_exists returns True when contact exists."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = self.mock_contact
        self.mock_db.query.return_value = mock_query

        # Act
        result = UserContacts.check_contact_exists(self.mock_db, self.user, self.contact_user)

        # Assert
        self.assertTrue(result)
        self.mock_db.query.assert_called_once_with(Contact)

    def test_check_contact_exists_false(self):
        """Test check_contact_exists returns False when contact does not exist."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        # Act
        result = UserContacts.check_contact_exists(self.mock_db, self.user, self.contact_user)

        # Assert
        self.assertFalse(result)
        self.mock_db.query.assert_called_once_with(Contact)

    @patch('app.business.user.user_contacts.UserValidators.search_user_by_identifier')
    def test_add_contact_success(self, mock_search_user):
        """Test successful contact addition."""
        # Arrange
        contact_create = ContactCreate(identifier="contactuser@example.com")
        mock_search_user.return_value = self.contact_user

        # Mock check_contact_exists to return False (contact doesn't exist)
        with patch.object(UserContacts, 'check_contact_exists', return_value=False):
            with patch.object(UserContacts, 'insert_contact', return_value=self.mock_contact) as mock_insert:
                # Act
                result = UserContacts.add_contact(self.mock_db, self.user, contact_create)

                # Assert
                self.assertEqual(result, self.mock_contact)
                mock_search_user.assert_called_once_with(self.mock_db, "contactuser@example.com")
                mock_insert.assert_called_once_with(self.mock_db, self.user, self.contact_user)

    @patch('app.business.user.user_contacts.UserValidators.search_user_by_identifier')
    def test_add_contact_strips_whitespace(self, mock_search_user):
        """Test that add_contact strips whitespace from identifier."""
        # Arrange
        contact_create = ContactCreate(identifier="  contactuser@example.com  ")
        mock_search_user.return_value = self.contact_user

        # Mock check_contact_exists to return False
        with patch.object(UserContacts, 'check_contact_exists', return_value=False):
            with patch.object(UserContacts, 'insert_contact', return_value=self.mock_contact):
                # Act
                UserContacts.add_contact(self.mock_db, self.user, contact_create)

                # Assert
                mock_search_user.assert_called_once_with(self.mock_db, "contactuser@example.com")

    @patch('app.business.user.user_contacts.UserValidators.search_user_by_identifier')
    def test_add_contact_already_exists(self, mock_search_user):
        """Test add_contact raises exception when contact already exists."""
        # Arrange
        contact_create = ContactCreate(identifier="contactuser@example.com")
        mock_search_user.return_value = self.contact_user

        # Mock check_contact_exists to return True (contact exists)
        with patch.object(UserContacts, 'check_contact_exists', return_value=True):
            # Act & Assert
            with self.assertRaises(HTTPException) as context:
                UserContacts.add_contact(self.mock_db, self.user, contact_create)

            self.assertEqual(context.exception.status_code, 400)
            self.assertEqual(context.exception.detail, "Contact already exists")

    @patch('app.business.user.user_contacts.UserValidators.search_user_by_identifier')
    def test_add_contact_user_not_found(self, mock_search_user):
        """Test add_contact when user validator raises exception for user not found."""
        # Arrange
        contact_create = ContactCreate(identifier="nonexistent@example.com")
        mock_search_user.side_effect = HTTPException(status_code=404, detail="User not found")

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            UserContacts.add_contact(self.mock_db, self.user, contact_create)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "User not found")

    def test_remove_contact_success(self):
        """Test successful contact removal."""
        # Arrange
        contact_id = 1

        # Act
        result = UserContacts.remove_contact(self.mock_db, self.user, contact_id)

        # Assert
        self.assertEqual(result, self.mock_contact)
        # Verify filter was called (without comparing SQLAlchemy expressions)
        self.user.contacts.filter.assert_called_once()
        self.mock_db.delete.assert_called_once_with(self.mock_contact)
        self.mock_db.commit.assert_called_once()

    def test_remove_contact_not_found(self):
        """Test remove_contact raises exception when contact not found."""
        # Arrange
        contact_id = 999
        contacts_query = Mock()
        contacts_query.filter.return_value.first.return_value = None
        self.user.contacts = contacts_query

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            UserContacts.remove_contact(self.mock_db, self.user, contact_id)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Contact not found")

        # Verify delete was not called
        self.mock_db.delete.assert_not_called()
        self.mock_db.commit.assert_not_called()

    def test_add_contact_with_empty_identifier(self):
        """Test add_contact with empty identifier after stripping."""
        # Arrange
        contact_create = ContactCreate(identifier="   ")

        with patch('app.business.user.user_contacts.UserValidators.search_user_by_identifier') as mock_search_user:
            mock_search_user.side_effect = HTTPException(status_code=400, detail="Invalid identifier")

            # Act & Assert
            with self.assertRaises(HTTPException) as context:
                UserContacts.add_contact(self.mock_db, self.user, contact_create)

            self.assertEqual(context.exception.status_code, 400)
            mock_search_user.assert_called_once_with(self.mock_db, "")

    def test_check_contact_exists_with_different_users(self):
        """Test check_contact_exists with different user combinations."""
        # Arrange
        other_user = self._create_mock_user(user_id=3, username="otheruser")
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        # Act
        result = UserContacts.check_contact_exists(self.mock_db, self.user, other_user)

        # Assert
        self.assertFalse(result)
        # Verify the filter was called (without comparing SQLAlchemy expressions)
        mock_query.filter.assert_called_once()

    def test_insert_contact_database_operations(self):
        """Test insert_contact performs correct database operations."""
        # Act
        UserContacts.insert_contact(self.mock_db, self.user, self.contact_user)

        # Assert - verify the correct sequence of database operations
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

        # Verify add was called with a Contact object
        call_args = self.mock_db.add.call_args
        if call_args and call_args[0]:
            added_contact = call_args[0][0]
            self.assertIsInstance(added_contact, Contact)
            self.assertEqual(added_contact.user_id, self.user.id)
            self.assertEqual(added_contact.contact_id, self.contact_user.id)


if __name__ == '__main__':
    unittest.main()