from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.business.withdrawal_service import WithdrawalService
from app.dependencies import get_db, get_user_except_pending_fpr
from app.models.user import User
from app.schemas.withdrawal import (
    WithdrawalCreate, WithdrawalUpdate, WithdrawalResponse,
    WithdrawalHistoryResponse, WithdrawalStatsResponse,
    RefundCreate, RefundResponse
)

router = APIRouter(tags=["Withdrawals"])


@router.post("/", response_model=WithdrawalResponse)
async def create_withdrawal(
        withdrawal_request: WithdrawalCreate,
        user: User = Depends(get_user_except_pending_fpr),
        db: Session = Depends(get_db)
):
    """Create a new withdrawal with comprehensive tracking"""
    return await WithdrawalService.create_withdrawal(db, user, withdrawal_request)


@router.post("/refund", response_model=RefundResponse)
async def create_refund(
        refund_request: RefundCreate,
        user: User = Depends(get_user_except_pending_fpr),
        db: Session = Depends(get_db)
):
    """Create a refund back to the original payment method"""
    return await WithdrawalService.create_refund(db, user, refund_request)


@router.get("/", response_model=WithdrawalHistoryResponse)
def get_user_withdrawals(
        limit: int = Query(50, ge=1, le=100),
        status: Optional[str] = Query(None,
                                      description="Filter by status: pending, processing, completed, failed, cancelled"),
        user: User = Depends(get_user_except_pending_fpr),
        db: Session = Depends(get_db)
):
    """Get withdrawal history for the current user with optional filtering"""
    return WithdrawalService.get_user_withdrawals(db, user, limit, status)


@router.get("/stats", response_model=WithdrawalStatsResponse)
def get_withdrawal_stats(
        user: User = Depends(get_user_except_pending_fpr),
        db: Session = Depends(get_db)
):
    """Get comprehensive withdrawal statistics for the current user"""
    return WithdrawalService.get_withdrawal_stats(db, user)


@router.get("/{withdrawal_id}", response_model=WithdrawalResponse)
def get_withdrawal(
        withdrawal_id: int,
        user: User = Depends(get_user_except_pending_fpr),
        db: Session = Depends(get_db)
):
    """Get a specific withdrawal by ID with full tracking details"""
    return WithdrawalService.get_withdrawal_by_id(db, user, withdrawal_id)


@router.put("/{withdrawal_id}", response_model=WithdrawalResponse)
def update_withdrawal_status(
        withdrawal_id: int,
        update_data: WithdrawalUpdate,
        user: User = Depends(get_user_except_pending_fpr),
        db: Session = Depends(get_db)
):
    """Update withdrawal status and tracking information"""
    return WithdrawalService.update_withdrawal_status(db, user, withdrawal_id, update_data)


@router.post("/{withdrawal_id}/cancel", response_model=WithdrawalResponse)
def cancel_withdrawal(
        withdrawal_id: int,
        user: User = Depends(get_user_except_pending_fpr),
        db: Session = Depends(get_db)
):
    """Cancel a pending withdrawal and refund the amount to user balance"""
    return WithdrawalService.cancel_withdrawal(db, user, withdrawal_id)
