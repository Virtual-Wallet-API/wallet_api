from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Category, User


class CategoryValidators:
    """Validation logic for category operations"""

    @staticmethod
    def validate_unique_category_name(db: Session, user_id: int, name: str, exclude_id: Optional[int] = None) -> None:
        """
        Validate that a category name is unique for the user.

        Args:
            db: Database session
            user_id: User ID to check uniqueness for
            name: Category name to validate
            exclude_id: Optional category ID to exclude from check (for updates)

        Raises:
            HTTPException: If category name already exists for the user
        """
        query = db.query(Category).filter(
            Category.user_id == user_id,
            Category.name.ilike(name.strip())  # Case-insensitive comparison
        )

        if exclude_id:
            query = query.filter(Category.id != exclude_id)

        existing_category = query.first()

        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with name '{name}' already exists. Please choose a different name."
            )

    @staticmethod
    def validate_category_ownership(db: Session, user_id: int, category_id: int) -> Category:
        """
        Validate that a category exists and belongs to the specified user.

        Args:
            db: Database session
            user_id: User ID to validate ownership for
            category_id: Category ID to validate

        Returns:
            Category: The validated category object

        Raises:
            HTTPException: If category not found or doesn't belong to user
        """
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == user_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found or you don't have permission to access it."
            )

        return category

    @staticmethod
    def validate_category_exists(db: Session, category_id: int) -> Category:
        """
        Validate that a category exists (without ownership check).

        Args:
            db: Database session
            category_id: Category ID to validate

        Returns:
            Category: The validated category object

        Raises:
            HTTPException: If category not found
        """
        category = db.query(Category).filter(Category.id == category_id).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found."
            )

        return category
