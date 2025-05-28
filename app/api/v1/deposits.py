from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.business.payment import *
from app.business.stripe import *
from app.dependencies import get_db, get_user_except_pending_fpr, get_user_except_fpr
from app.models.user import User
from app.schemas.deposit import (
    DepositWithCard, DepositResponse, DepositHistoryResponse, DepositStatsResponse, DepositPaymentIntentCreate,
    DepositPaymentIntentResponse, DepositConfirm
)

router = APIRouter(tags=["Deposits"])


@router.post("/payment-intent", response_model=DepositPaymentIntentResponse)
async def create_deposit_payment_intent(
        deposit_data: DepositPaymentIntentCreate,
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Create a payment intent for a new deposit (with new card)"""
    return await StripeDepositService.create_deposit_payment_intent(db, user, deposit_data)


@router.post("/with-card", response_model=DepositPaymentIntentResponse)
async def deposit_with_existing_card(
        deposit_data: DepositWithCard,
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Create a deposit using an existing saved card"""
    return await StripeDepositService.deposit_with_existing_card(db, user, deposit_data)


@router.post("/confirm", response_model=DepositResponse)
async def confirm_deposit(
        confirm_data: DepositConfirm,
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Confirm a deposit and update user balance"""
    return await StripeDepositService.confirm_deposit(db, user, confirm_data)


@router.get("/", response_model=DepositHistoryResponse)
def get_user_deposits(
        limit: int = 50,
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Get deposit history for the current user"""
    return DepositService.get_user_deposits(db, user, limit)


@router.get("/stats", response_model=DepositStatsResponse)
def get_deposit_stats(
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Get deposit statistics for the current user"""
    return DepositService.get_deposit_stats(db, user)


@router.get("/{deposit_id}", response_model=DepositResponse)
def get_deposit(
        deposit_id: int,
        user: User = Depends(get_user_except_pending_fpr),
        db: Session = Depends(get_db)
):
    """Get a specific deposit by ID"""
    return DepositService.get_deposit_by_id(db, user, deposit_id)
