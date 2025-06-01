"""
Unit tests for CategoryService business logic.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from tests.base_test import BaseTestCase
from app.business.category.category_service import CategoryService
from app.models import Category, User, Transaction
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate


class TestCategoryService(BaseTestCase):
    """Test cases for CategoryService."""

    def setUp(self):
        super().setUp()
        self.category_data = CategoryCreate(
            name="TestCategory",  # Fixed: alphanumeric only, no spaces
            description="Test category description"
        )

        self.mock_category = self._create_mock_category()
        self.mock_category.total_income = 500.0
        self.mock_category.total_expense = 300.0
        self.mock_category.total_transactions = 5
        self.mock_category.completed_transactions = 3
        self.mock_category.total_amount = 800.0

    @patch('app.business.category.category_validators.CategoryValidators.validate_unique_category_name')
    @patch('app.schemas.category.CategoryResponse.model_validate')
    def test_create_category_success(self, mock_model_validate, mock_validate_unique):
        """Test successful category creation."""
        # Arrange
        mock_validate_unique.return_value = None  # No validation errors
        mock_response = {'id': 1, 'name': 'TestCategory', 'description': 'Test category description'}
        mock_model_validate.return_value = mock_response

        # Act
        result = CategoryService.create_category(self.mock_db, self.mock_user, self.category_data)

        # Assert
        mock_validate_unique.assert_called_once_with(self.mock_db, self.mock_user.id, "TestCategory")
        self.assert_db_add_called_with_type(Category)
        self.assert_db_operations_called(add=True, commit=True, refresh=True)
        self.assertEqual(result, mock_response)

    @patch('app.business.category.category_validators.CategoryValidators.validate_unique_category_name')
    def test_create_category_duplicate_name(self, mock_validate_unique):
        """Test category creation fails with duplicate name."""
        # Arrange
        mock_validate_unique.side_effect = HTTPException(status_code=400, detail="Category name already exists")

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            CategoryService.create_category(self.mock_db, self.mock_user, self.category_data)

        self.assertEqual(context.exception.status_code, 400)
        self.mock_db.add.assert_not_called()

    def test_get_user_categories_without_search(self):
        """Test getting user categories without search filter."""
        # Arrange
        mock_categories = [
            self._create_mock_category(1, name="Category1"),
            self._create_mock_category(2, name="Category2"),
            self._create_mock_category(3, name="Category3")
        ]

        # Set up mock properties for statistics
        for cat in mock_categories:
            cat.total_income = 100.0
            cat.total_expense = 50.0
            cat.total_transactions = 2

        query_mock = self.setup_db_query_mock(Category, mock_categories)
        query_mock.count.return_value = 3

        # Mock the CategoryResponse.model_validate to avoid validation
        with patch('app.schemas.category.CategoryResponse.model_validate') as mock_validate:
            mock_validate.side_effect = lambda cat: {'id': cat.id, 'name': cat.name}

            # Act
            result = CategoryService.get_user_categories(self.mock_db, self.mock_user)

        # Assert
        self.mock_db.query.assert_called_with(Category)
        self.assertEqual(len(result["categories"]), 3)
        self.assertEqual(result["total_count"], 3)
        self.assertEqual(result["returned_count"], 3)
        self.assertEqual(result["total_income"], 300.0)
        self.assertEqual(result["total_expense"], 150.0)
        self.assertEqual(result["total_transactions"], 6)
        self.assertFalse(result["has_more"])

    def test_get_user_categories_with_search(self):
        """Test getting user categories with search filter."""
        # Arrange
        mock_categories = [self._create_mock_category(1, name="TestCategory")]
        mock_categories[0].total_income = 100.0
        mock_categories[0].total_expense = 50.0
        mock_categories[0].total_transactions = 2

        query_mock = self.setup_db_query_mock(Category, mock_categories)
        query_mock.count.return_value = 1

        # Mock the CategoryResponse.model_validate to avoid validation
        with patch('app.schemas.category.CategoryResponse.model_validate') as mock_validate:
            mock_validate.side_effect = lambda cat: {'id': cat.id, 'name': cat.name}

            # Act
            result = CategoryService.get_user_categories(
                self.mock_db, self.mock_user, search="Test", limit=10, offset=0
            )

        # Assert
        # Verify the search filters were applied
        filter_calls = query_mock.filter.call_args_list
        self.assertTrue(len(filter_calls) >= 2)  # user_id filter + search filter
        self.assertEqual(len(result["categories"]), 1)
        self.assertEqual(result["total_count"], 1)

    def test_get_user_categories_with_pagination(self):
        """Test getting user categories with pagination showing more results."""
        # Arrange
        mock_categories = [self._create_mock_category(i) for i in range(1, 6)]  # 5 categories
        for cat in mock_categories:
            cat.total_income = 100.0
            cat.total_expense = 50.0
            cat.total_transactions = 2

        query_mock = self.setup_db_query_mock(Category, mock_categories)
        query_mock.count.return_value = 10  # Total 10 categories

        # Mock the CategoryResponse.model_validate to avoid validation
        with patch('app.schemas.category.CategoryResponse.model_validate') as mock_validate:
            mock_validate.side_effect = lambda cat: {'id': cat.id, 'name': cat.name}

            # Act
            result = CategoryService.get_user_categories(
                self.mock_db, self.mock_user, limit=5, offset=0
            )

        # Assert
        self.assertEqual(result["total_count"], 10)
        self.assertEqual(result["returned_count"], 5)
        self.assertTrue(result["has_more"])

    @patch('app.business.category.category_validators.CategoryValidators.validate_category_ownership')
    @patch('app.schemas.category.CategoryResponse.model_validate')
    def test_get_category_by_id_success(self, mock_model_validate, mock_validate_ownership):
        """Test successful retrieval of category by ID."""
        # Arrange
        mock_validate_ownership.return_value = self.mock_category
        mock_response = {'id': 1, 'name': 'TestCategory'}
        mock_model_validate.return_value = mock_response

        # Act
        result = CategoryService.get_category_by_id(self.mock_db, self.mock_user, 1)

        # Assert
        mock_validate_ownership.assert_called_once_with(self.mock_db, self.mock_user.id, 1)
        self.assertEqual(result, mock_response)

    @patch('app.business.category.category_validators.CategoryValidators.validate_category_ownership')
    def test_get_category_by_id_not_found(self, mock_validate_ownership):
        """Test category retrieval when category not found."""
        # Arrange
        mock_validate_ownership.side_effect = HTTPException(status_code=404, detail="Category not found")

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            CategoryService.get_category_by_id(self.mock_db, self.mock_user, 999)

        self.assertEqual(context.exception.status_code, 404)

    @patch('app.business.category.category_validators.CategoryValidators.validate_category_ownership')
    @patch('app.business.category.category_validators.CategoryValidators.validate_unique_category_name')
    @patch('app.schemas.category.CategoryResponse.model_validate')
    def test_update_category_success(self, mock_model_validate, mock_validate_unique, mock_validate_ownership):
        """Test successful category update."""
        # Arrange
        self.mock_category.name = "OriginalName"
        mock_validate_ownership.return_value = self.mock_category
        mock_validate_unique.return_value = None
        mock_response = {'id': 1, 'name': 'UpdatedCategory'}
        mock_model_validate.return_value = mock_response

        update_data = CategoryUpdate(
            name="UpdatedCategory",
            description="Updated description"
        )

        # Act
        result = CategoryService.update_category(self.mock_db, self.mock_user, 1, update_data)

        # Assert
        mock_validate_ownership.assert_called_once_with(self.mock_db, self.mock_user.id, 1)
        mock_validate_unique.assert_called_once_with(self.mock_db, self.mock_user.id, "UpdatedCategory")

        self.assertEqual(self.mock_category.name, "UpdatedCategory")
        self.assertEqual(self.mock_category.description, "Updated description")
        self.assert_db_operations_called(add=False, commit=True, refresh=True)
        self.assertEqual(result, mock_response)

    @patch('app.business.category.category_validators.CategoryValidators.validate_category_ownership')
    @patch('app.schemas.category.CategoryResponse.model_validate')
    def test_update_category_same_name_no_validation(self, mock_model_validate, mock_validate_ownership):
        """Test category update with same name doesn't trigger unique validation."""
        # Arrange
        self.mock_category.name = "SameName"
        mock_validate_ownership.return_value = self.mock_category
        mock_response = {'id': 1, 'name': 'SameName'}
        mock_model_validate.return_value = mock_response

        update_data = CategoryUpdate(
            name="SameName",  # Same name
            description="Updated description"
        )

        # Act
        with patch('app.business.category.category_validators.CategoryValidators.validate_unique_category_name') as mock_validate_unique:
            result = CategoryService.update_category(self.mock_db, self.mock_user, 1, update_data)

            # Assert
            mock_validate_unique.assert_not_called()  # Should not be called for same name

    @patch('app.business.category.category_validators.CategoryValidators.validate_category_ownership')
    @patch('app.business.category.category_validators.CategoryValidators.validate_unique_category_name')
    def test_update_category_duplicate_name(self, mock_validate_unique, mock_validate_ownership):
        """Test category update fails with duplicate name."""
        # Arrange
        self.mock_category.name = "OriginalName"
        mock_validate_ownership.return_value = self.mock_category
        mock_validate_unique.side_effect = HTTPException(status_code=400, detail="Category name already exists")

        update_data = CategoryUpdate(
            name="DuplicateCategory",
            description="Updated description"
        )

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            CategoryService.update_category(self.mock_db, self.mock_user, 1, update_data)

        self.assertEqual(context.exception.status_code, 400)

    @patch('app.business.category.category_validators.CategoryValidators.validate_category_ownership')
    def test_delete_category_success(self, mock_validate_ownership):
        """Test successful category deletion."""
        # Arrange
        category_with_no_transactions = self._create_mock_category()
        category_with_no_transactions.total_transactions = 0
        mock_validate_ownership.return_value = category_with_no_transactions

        # Act
        CategoryService.delete_category(self.mock_db, self.mock_user, 1)

        # Assert
        mock_validate_ownership.assert_called_once_with(self.mock_db, self.mock_user.id, 1)
        self.mock_db.delete.assert_called_once_with(category_with_no_transactions)
        self.mock_db.commit.assert_called_once()

    @patch('app.business.category.category_validators.CategoryValidators.validate_category_ownership')
    def test_delete_category_with_transactions(self, mock_validate_ownership):
        """Test category deletion fails when category has transactions."""
        # Arrange
        category_with_transactions = self._create_mock_category()
        category_with_transactions.total_transactions = 5
        category_with_transactions.name = "CategoryWithTransactions"
        mock_validate_ownership.return_value = category_with_transactions

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            CategoryService.delete_category(self.mock_db, self.mock_user, 1)

        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("Cannot delete category", context.exception.detail)
        self.assertIn("5 associated transactions", context.exception.detail)
        self.mock_db.delete.assert_not_called()

    @patch('app.business.category.category_validators.CategoryValidators.validate_category_ownership')
    @patch('app.schemas.category.CategoryResponse.model_validate')
    def test_get_category_statistics_success(self, mock_model_validate, mock_validate_ownership):
        """Test successful retrieval of category statistics."""
        # Arrange
        mock_category = self._create_mock_category()
        mock_category.total_income = 500.0
        mock_category.total_expense = 300.0
        mock_category.total_transactions = 10
        mock_category.completed_transactions = 7
        mock_category.total_amount = 800.0

        # Mock transactions with different statuses - simplified without full validation
        mock_transactions = []

        # 5 completed transactions (3 income, 2 expense)
        for i in range(5):
            tx = Mock()
            tx.is_completed = True
            tx.is_failed = False
            tx.is_income = Mock(return_value=i < 3)  # First 3 are income
            tx.is_expense = Mock(return_value=i >= 3)  # Last 2 are expense
            mock_transactions.append(tx)

        # 2 pending transactions
        for i in range(2):
            tx = Mock()
            tx.is_completed = False
            tx.is_failed = False
            mock_transactions.append(tx)

        # 1 failed transaction
        tx = Mock()
        tx.is_completed = False
        tx.is_failed = True
        mock_transactions.append(tx)

        mock_category.transactions = mock_transactions
        mock_validate_ownership.return_value = mock_category
        mock_model_validate.return_value = {'id': 1, 'name': 'TestCategory'}

        # Act
        result = CategoryService.get_category_statistics(self.mock_db, self.mock_user, 1)

        # Assert
        mock_validate_ownership.assert_called_once_with(self.mock_db, self.mock_user.id, 1)
        self.assertIn("category", result)
        self.assertIn("statistics", result)

        stats = result["statistics"]
        self.assertEqual(stats["total_transactions"], 10)
        self.assertEqual(stats["completed_transactions"], 5)
        self.assertEqual(stats["pending_transactions"], 2)
        self.assertEqual(stats["failed_transactions"], 1)
        self.assertEqual(stats["income_transactions"], 3)
        self.assertEqual(stats["expense_transactions"], 2)
        self.assertEqual(stats["total_income"], 500.0)
        self.assertEqual(stats["total_expense"], 300.0)
        self.assertEqual(stats["net_amount"], 200.0)  # 500 - 300

    def test_get_categories_summary_with_categories(self):
        """Test successful retrieval of categories summary with data."""
        # Arrange
        mock_categories = [
            self._create_mock_category(1, name="Food"),
            self._create_mock_category(2, name="Transportation"),
            self._create_mock_category(3, name="Entertainment")
        ]

        # Set up statistics for each category
        for i, cat in enumerate(mock_categories):
            cat.total_income = (i + 1) * 100.0  # 100, 200, 300
            cat.total_expense = (i + 1) * 50.0   # 50, 100, 150
            cat.completed_transactions = (i + 1) * 2  # 2, 4, 6
            cat.total_amount = cat.total_income + cat.total_expense

        query_mock = self.setup_db_query_mock(Category, mock_categories)

        # Act
        result = CategoryService.get_categories_summary(self.mock_db, self.mock_user)

        # Assert
        self.mock_db.query.assert_called_with(Category)
        self.assertEqual(result["total_categories"], 3)
        self.assertEqual(result["total_income"], 600.0)  # 100+200+300
        self.assertEqual(result["total_expense"], 300.0)  # 50+100+150
        self.assertEqual(result["net_amount"], 300.0)     # 600-300

        # Check top categories
        self.assertEqual(len(result["top_income_categories"]), 3)
        self.assertEqual(len(result["top_expense_categories"]), 3)
        self.assertEqual(len(result["most_used_categories"]), 3)

        # Verify sorting (highest income first)
        top_income = result["top_income_categories"]
        self.assertEqual(top_income[0]["total_income"], 300.0)  # Entertainment
        self.assertEqual(top_income[1]["total_income"], 200.0)  # Transportation
        self.assertEqual(top_income[2]["total_income"], 100.0)  # Food

    def test_get_categories_summary_empty(self):
        """Test categories summary when no categories exist."""
        # Arrange
        query_mock = self.setup_db_query_mock(Category, [])

        # Act
        result = CategoryService.get_categories_summary(self.mock_db, self.mock_user)

        # Assert
        self.mock_db.query.assert_called_with(Category)
        self.assertEqual(result["total_categories"], 0)
        self.assertEqual(result["total_income"], 0.0)
        self.assertEqual(result["total_expense"], 0.0)
        self.assertEqual(result["net_amount"], 0.0)
        self.assertEqual(result["top_income_categories"], [])
        self.assertEqual(result["top_expense_categories"], [])
        self.assertEqual(result["most_used_categories"], [])

    def test_get_user_categories_empty_result(self):
        """Test getting user categories when no categories exist."""
        # Arrange
        query_mock = self.setup_db_query_mock(Category, [])
        query_mock.count.return_value = 0

        # Act
        result = CategoryService.get_user_categories(self.mock_db, self.mock_user)

        # Assert
        self.assertEqual(len(result["categories"]), 0)
        self.assertEqual(result["total_count"], 0)
        self.assertEqual(result["returned_count"], 0)
        self.assertEqual(result["total_income"], 0)
        self.assertEqual(result["total_expense"], 0)
        self.assertEqual(result["total_transactions"], 0)
        self.assertFalse(result["has_more"])

    def test_get_categories_summary_filters_zero_amounts(self):
        """Test that categories summary filters out categories with zero amounts."""
        # Arrange
        mock_categories = [
            self._create_mock_category(1, name="ActiveCategory"),
            self._create_mock_category(2, name="EmptyCategory"),
        ]

        # First category has activity
        mock_categories[0].total_income = 100.0
        mock_categories[0].total_expense = 50.0
        mock_categories[0].completed_transactions = 5

        # Second category has no activity
        mock_categories[1].total_income = 0.0
        mock_categories[1].total_expense = 0.0
        mock_categories[1].completed_transactions = 0

        query_mock = self.setup_db_query_mock(Category, mock_categories)

        # Act
        result = CategoryService.get_categories_summary(self.mock_db, self.mock_user)

        # Assert
        self.assertEqual(result["total_categories"], 2)
        # Only active categories should appear in top lists
        self.assertEqual(len(result["top_income_categories"]), 1)
        self.assertEqual(len(result["top_expense_categories"]), 1)
        self.assertEqual(len(result["most_used_categories"]), 1)


if __name__ == '__main__':
    unittest.main() 