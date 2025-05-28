from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models import Category, User, Transaction
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.business.category.category_validators import CategoryValidators


class CategoryService:
    """Business logic for category management operations"""

    @staticmethod
    def create_category(db: Session, user: User, category_data: CategoryCreate) -> CategoryResponse:
        """
        Create a new category for the authenticated user.

        Args:
            db: Database session
            user: Authenticated user
            category_data: Category creation data

        Returns:
            CategoryResponse: Created category with metadata

        Raises:
            HTTPException: If category name already exists for user
        """
        # Validate category doesn't already exist for this user
        CategoryValidators.validate_unique_category_name(db, user.id, category_data.name)

        # Create new category
        db_category = Category(
            name=category_data.name,
            description=category_data.description,
            user_id=user.id
        )

        db.add(db_category)
        db.commit()
        db.refresh(db_category)

        return CategoryResponse.model_validate(db_category)

    @staticmethod
    def get_user_categories(
            db: Session,
            user: User,
            search: Optional[str] = None,
            limit: int = 50,
            offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get all categories for a user with optional search and pagination.

        Args:
            db: Database session
            user: Authenticated user
            search: Optional search term for category name/description
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Dict containing categories list and metadata
        """
        query = db.query(Category).filter(Category.user_id == user.id)

        # Apply search filter if provided
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Category.name).like(search_term),
                    func.lower(Category.description).like(search_term)
                )
            )

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination and ordering
        categories = query.order_by(Category.name.asc()).offset(offset).limit(limit).all()

        # Calculate summary statistics
        total_income = sum(cat.total_income for cat in categories)
        total_expense = sum(cat.total_expense for cat in categories)
        total_transactions = sum(cat.total_transactions for cat in categories)

        return {
            "categories": [CategoryResponse.model_validate(cat) for cat in categories],
            "total_count": total_count,
            "returned_count": len(categories),
            "total_income": total_income,
            "total_expense": total_expense,
            "total_transactions": total_transactions,
            "has_more": (offset + len(categories)) < total_count
        }

    @staticmethod
    def get_category_by_id(db: Session, user: User, category_id: int) -> CategoryResponse:
        """
        Get a specific category by ID for the authenticated user.

        Args:
            db: Database session
            user: Authenticated user
            category_id: Category ID to retrieve

        Returns:
            CategoryResponse: Category with full details

        Raises:
            HTTPException: If category not found or doesn't belong to user
        """
        category = CategoryValidators.validate_category_ownership(db, user.id, category_id)
        return CategoryResponse.model_validate(category)

    @staticmethod
    def update_category(
            db: Session,
            user: User,
            category_id: int,
            update_data: CategoryUpdate
    ) -> CategoryResponse:
        """
        Update an existing category for the authenticated user.

        Args:
            db: Database session
            user: Authenticated user
            category_id: Category ID to update
            update_data: Updated category data

        Returns:
            CategoryResponse: Updated category

        Raises:
            HTTPException: If category not found, doesn't belong to user, or name conflicts
        """
        # Validate category exists and belongs to user
        category = CategoryValidators.validate_category_ownership(db, user.id, category_id)

        # Validate new name is unique (if changed)
        if update_data.name != category.name:
            CategoryValidators.validate_unique_category_name(db, user.id, update_data.name)

        # Update category fields
        category.name = update_data.name
        category.description = update_data.description

        db.commit()
        db.refresh(category)

        return CategoryResponse.model_validate(category)

    @staticmethod
    def delete_category(db: Session, user: User, category_id: int) -> None:
        """
        Delete a category for the authenticated user.

        Args:
            db: Database session
            user: Authenticated user
            category_id: Category ID to delete

        Raises:
            HTTPException: If category not found, doesn't belong to user, or has transactions
        """
        # Validate category exists and belongs to user
        category = CategoryValidators.validate_category_ownership(db, user.id, category_id)

        # Check if category has transactions
        if category.total_transactions > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete category '{category.name}' because it has {category.total_transactions} associated transactions. "
                       "Please reassign or delete the transactions first."
            )

        db.delete(category)
        db.commit()

    @staticmethod
    def get_category_statistics(db: Session, user: User, category_id: int) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific category.

        Args:
            db: Database session
            user: Authenticated user
            category_id: Category ID to get statistics for

        Returns:
            Dict containing detailed category statistics

        Raises:
            HTTPException: If category not found or doesn't belong to user
        """
        category = CategoryValidators.validate_category_ownership(db, user.id, category_id)

        # Get transaction statistics
        completed_transactions = [t for t in category.transactions if t.is_completed]
        pending_transactions = [t for t in category.transactions if not t.is_completed and not t.is_failed]
        failed_transactions = [t for t in category.transactions if t.is_failed]

        income_transactions = [t for t in completed_transactions if t.is_income(user.id)]
        expense_transactions = [t for t in completed_transactions if t.is_expense(user.id)]

        return {
            "category": CategoryResponse.model_validate(category),
            "statistics": {
                "total_transactions": category.total_transactions,
                "completed_transactions": len(completed_transactions),
                "pending_transactions": len(pending_transactions),
                "failed_transactions": len(failed_transactions),
                "income_transactions": len(income_transactions),
                "expense_transactions": len(expense_transactions),
                "total_income": category.total_income,
                "total_expense": category.total_expense,
                "net_amount": category.total_income - category.total_expense,
                "average_transaction_amount": (
                    category.total_amount / len(completed_transactions)
                    if completed_transactions else 0
                )
            }
        }

    @staticmethod
    def get_categories_summary(db: Session, user: User) -> Dict[str, Any]:
        """
        Get a summary of all categories for the user.

        Args:
            db: Database session
            user: Authenticated user

        Returns:
            Dict containing categories summary and top categories by usage
        """
        categories = db.query(Category).filter(Category.user_id == user.id).all()

        if not categories:
            return {
                "total_categories": 0,
                "total_income": 0.0,
                "total_expense": 0.0,
                "net_amount": 0.0,
                "top_income_categories": [],
                "top_expense_categories": [],
                "most_used_categories": []
            }

        # Calculate totals
        total_income = sum(cat.total_income for cat in categories)
        total_expense = sum(cat.total_expense for cat in categories)

        # Sort categories by different metrics
        top_income = sorted(categories, key=lambda x: x.total_income, reverse=True)[:5]
        top_expense = sorted(categories, key=lambda x: x.total_expense, reverse=True)[:5]
        most_used = sorted(categories, key=lambda x: x.completed_transactions, reverse=True)[:5]

        return {
            "total_categories": len(categories),
            "total_income": total_income,
            "total_expense": total_expense,
            "net_amount": total_income - total_expense,
            "top_income_categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "total_income": cat.total_income,
                    "transaction_count": cat.completed_transactions
                }
                for cat in top_income if cat.total_income > 0
            ],
            "top_expense_categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "total_expense": cat.total_expense,
                    "transaction_count": cat.completed_transactions
                }
                for cat in top_expense if cat.total_expense > 0
            ],
            "most_used_categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "transaction_count": cat.completed_transactions,
                    "total_amount": cat.total_amount
                }
                for cat in most_used if cat.completed_transactions > 0
            ]
        }