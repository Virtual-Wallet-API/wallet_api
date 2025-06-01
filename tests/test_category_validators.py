"""
Unit tests for CategoryValidators business logic.
"""
import unittest
from unittest.mock import Mock
from fastapi import HTTPException

from tests.base_test import BaseTestCase
from app.business.category.category_validators import CategoryValidators
from app.models import Category


class TestCategoryValidators(BaseTestCase):
    """Test cases for CategoryValidators."""

    def setUp(self):
        super().setUp()
        self.user_id = 1
        self.category_id = 1
        self.category_name = "TestCategory"

        # Create mock category
        self.mock_category = self._create_mock_category(
            category_id=self.category_id,
            name=self.category_name,
            user_id=self.user_id
        )

    def test_validate_unique_category_name_success(self):
        """Test successful unique category name validation when no duplicate exists."""
        # Setup query mock to return None (no existing category)
        query_mock = self.setup_db_query_mock(Category, [])
        query_mock.first.return_value = None

        # Should not raise any exception
        CategoryValidators.validate_unique_category_name(
            self.mock_db, self.user_id, self.category_name
        )

        # Verify database query was called correctly
        self.mock_db.query.assert_called_with(Category)
        query_mock.filter.assert_called()

    def test_validate_unique_category_name_duplicate_exists(self):
        """Test unique category name validation fails when duplicate exists."""
        # Setup query mock to return existing category
        query_mock = self.setup_db_query_mock(Category, self.mock_category)
        query_mock.first.return_value = self.mock_category

        with self.assertRaises(HTTPException) as context:
            CategoryValidators.validate_unique_category_name(
                self.mock_db, self.user_id, self.category_name
            )

        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("already exists", context.exception.detail)
        self.assertIn(self.category_name, context.exception.detail)

    def test_validate_unique_category_name_with_exclude_id(self):
        """Test unique category name validation with exclude_id parameter."""
        # Setup query mock to return None (no duplicate after excluding current)
        query_mock = self.setup_db_query_mock(Category, [])
        query_mock.first.return_value = None

        exclude_id = 2
        CategoryValidators.validate_unique_category_name(
            self.mock_db, self.user_id, self.category_name, exclude_id
        )

        # Verify exclude filter was applied
        self.mock_db.query.assert_called_with(Category)
        query_mock.filter.assert_called()

    def test_validate_unique_category_name_case_insensitive(self):
        """Test that category name validation is case-insensitive."""
        # Setup query mock to return existing category
        query_mock = self.setup_db_query_mock(Category, self.mock_category)
        query_mock.first.return_value = self.mock_category

        with self.assertRaises(HTTPException) as context:
            CategoryValidators.validate_unique_category_name(
                self.mock_db, self.user_id, "TESTCATEGORY"  # Different case
            )

        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("already exists", context.exception.detail)

    def test_validate_unique_category_name_with_whitespace(self):
        """Test that category name validation strips whitespace."""
        # Setup query mock to return existing category
        query_mock = self.setup_db_query_mock(Category, self.mock_category)
        query_mock.first.return_value = self.mock_category

        with self.assertRaises(HTTPException) as context:
            CategoryValidators.validate_unique_category_name(
                self.mock_db, self.user_id, "  TestCategory  "  # With whitespace
            )

        self.assertEqual(context.exception.status_code, 409)

    def test_validate_category_ownership_success(self):
        """Test successful category ownership validation."""
        # Setup query mock to return owned category
        query_mock = self.setup_db_query_mock(Category, self.mock_category)
        query_mock.first.return_value = self.mock_category

        result = CategoryValidators.validate_category_ownership(
            self.mock_db, self.user_id, self.category_id
        )

        self.assertEqual(result, self.mock_category)
        self.mock_db.query.assert_called_with(Category)

    def test_validate_category_ownership_not_found(self):
        """Test category ownership validation fails when category not found."""
        # Setup query mock to return None
        query_mock = self.setup_db_query_mock(Category, [])
        query_mock.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            CategoryValidators.validate_category_ownership(
                self.mock_db, self.user_id, 999
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("not found", context.exception.detail)
        self.assertIn("don't have permission", context.exception.detail)

    def test_validate_category_ownership_wrong_user(self):
        """Test category ownership validation fails for wrong user."""
        # Setup query mock to return None (as if category doesn't belong to user)
        query_mock = self.setup_db_query_mock(Category, [])
        query_mock.first.return_value = None

        wrong_user_id = 999
        with self.assertRaises(HTTPException) as context:
            CategoryValidators.validate_category_ownership(
                self.mock_db, wrong_user_id, self.category_id
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("not found", context.exception.detail)

    def test_validate_category_exists_success(self):
        """Test successful category existence validation."""
        # Setup query mock to return category
        query_mock = self.setup_db_query_mock(Category, self.mock_category)
        query_mock.first.return_value = self.mock_category

        result = CategoryValidators.validate_category_exists(
            self.mock_db, self.category_id
        )

        self.assertEqual(result, self.mock_category)
        self.mock_db.query.assert_called_with(Category)

    def test_validate_category_exists_not_found(self):
        """Test category existence validation fails when category not found."""
        # Setup query mock to return None
        query_mock = self.setup_db_query_mock(Category, [])
        query_mock.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            CategoryValidators.validate_category_exists(
                self.mock_db, 999
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("not found", context.exception.detail)
        # Should not mention permission (unlike ownership validation)
        self.assertNotIn("permission", context.exception.detail)

    def test_validate_category_exists_vs_ownership_difference(self):
        """Test that category_exists doesn't check ownership while ownership does."""
        # Setup query mocks
        query_mock = self.setup_db_query_mock(Category, self.mock_category)
        query_mock.first.return_value = self.mock_category

        # validate_category_exists should succeed regardless of user_id in category
        result = CategoryValidators.validate_category_exists(
            self.mock_db, self.category_id
        )
        self.assertEqual(result, self.mock_category)

        # Reset mock for next test
        self.mock_db.reset_mock()
        query_mock = self.setup_db_query_mock(Category, self.mock_category)
        query_mock.first.return_value = self.mock_category

        # validate_category_ownership should also succeed for correct user
        result = CategoryValidators.validate_category_ownership(
            self.mock_db, self.user_id, self.category_id
        )
        self.assertEqual(result, self.mock_category)

    def test_validate_unique_category_name_exclude_works(self):
        """Test that exclude_id properly excludes the specified category."""
        # Create a second mock category that would be excluded
        excluded_category = self._create_mock_category(
            category_id=2,
            name=self.category_name,
            user_id=self.user_id
        )

        # Setup query mock to return empty result (excluded category not found)
        query_mock = self.setup_db_query_mock(Category, [])
        query_mock.first.return_value = None

        # Should not raise exception when excluding the category with same name
        CategoryValidators.validate_unique_category_name(
            self.mock_db, self.user_id, self.category_name, exclude_id=2
        )

        # Verify multiple filter calls were made (user_id, name, exclude_id)
        self.mock_db.query.assert_called_with(Category)
        self.assertTrue(query_mock.filter.call_count >= 2)

    def test_validate_category_ownership_exact_match(self):
        """Test that category ownership validation checks both ID and user_id."""
        # Setup query mock to return category
        query_mock = self.setup_db_query_mock(Category, self.mock_category)
        query_mock.first.return_value = self.mock_category

        result = CategoryValidators.validate_category_ownership(
            self.mock_db, self.user_id, self.category_id
        )

        self.assertEqual(result, self.mock_category)
        # Should filter by both category ID and user ID
        self.mock_db.query.assert_called_with(Category)
        self.assertTrue(query_mock.filter.call_count >= 1)


if __name__ == '__main__':
    unittest.main()