from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.business.category import CategoryService
from app.dependencies import get_db, get_user_except_pending_fpr
from app.models import User
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryDetailResponse,
    CategoryListResponse,
    CategoryStatisticsResponse,
    CategorySummaryResponse
)

router = APIRouter(tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
        category_data: CategoryCreate,
        db: Session = Depends(get_db),
        user: User = Depends(get_user_except_pending_fpr)
):
    """
    Create a new category for the authenticated user.

    - **name**: Category name (3-32 characters, alphanumeric only, must be unique for the user)
    - **description**: Optional category description (max 120 characters, alphanumeric with commas, periods, and spaces)

    Returns the created category with basic information.
    """
    return CategoryService.create_category(db, user, category_data)


@router.get("/", response_model=CategoryListResponse)
def get_categories(
        db: Session = Depends(get_db),
        user: User = Depends(get_user_except_pending_fpr),
        search: Optional[str] = Query(None, description="Search categories by name or description"),
        limit: int = Query(50, ge=1, le=100, description="Maximum number of categories to return"),
        offset: int = Query(0, ge=0, description="Number of categories to skip")
):
    """
    Get all categories for the authenticated user with optional search and pagination.

    - **search**: Optional search term to filter categories by name or description
    - **limit**: Maximum number of results (1-100, default: 50)
    - **offset**: Number of results to skip for pagination (default: 0)

    Returns a paginated list of categories with summary statistics.
    """
    return CategoryService.get_user_categories(db, user, search, limit, offset)


@router.get("/summary", response_model=CategorySummaryResponse)
def get_categories_summary(
        db: Session = Depends(get_db),
        user: User = Depends(get_user_except_pending_fpr)
):
    """
    Get a summary of all categories for the authenticated user.

    Returns summary statistics including:
    - Total categories count
    - Total income and expense amounts
    - Top categories by income, expense, and usage
    """
    return CategoryService.get_categories_summary(db, user)


@router.get("/{category_id}", response_model=CategoryDetailResponse)
def get_category(
        category_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_user_except_pending_fpr)
):
    """
    Get a specific category by ID for the authenticated user.

    - **category_id**: The ID of the category to retrieve

    Returns detailed category information including associated transactions.
    """
    return CategoryService.get_category_by_id(db, user, category_id)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
        category_id: int,
        update_data: CategoryUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(get_user_except_pending_fpr)
):
    """
    Update an existing category for the authenticated user.

    - **category_id**: The ID of the category to update
    - **name**: New category name (3-32 characters, alphanumeric only, must be unique for the user)
    - **description**: New category description (max 120 characters, alphanumeric with commas, periods, and spaces)

    Returns the updated category information.
    """
    return CategoryService.update_category(db, user, category_id, update_data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
        category_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_user_except_pending_fpr)
):
    """
    Delete a category for the authenticated user.

    - **category_id**: The ID of the category to delete

    Note: Categories with associated transactions cannot be deleted.
    You must reassign or delete the transactions first.
    """
    CategoryService.delete_category(db, user, category_id)


@router.get("/{category_id}/statistics", response_model=CategoryStatisticsResponse)
def get_category_statistics(
        category_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_user_except_pending_fpr)
):
    """
    Get detailed statistics for a specific category.

    - **category_id**: The ID of the category to get statistics for

    Returns comprehensive statistics including:
    - Transaction counts by status (completed, pending, failed)
    - Income vs expense breakdown
    - Average transaction amounts
    - Net amount calculations
    """
    return CategoryService.get_category_statistics(db, user, category_id)
