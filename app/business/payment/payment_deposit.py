import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.deposit import Deposit
from app.models.user import User
from app.schemas.deposit import (
    DepositResponse,
    DepositStatsResponse
)

logger = logging.getLogger(__name__)


class DepositService:
    """Business logic for core deposit management"""

    @staticmethod
    def get_user_deposits(db: Session, user: User, limit: int = 30, page: int = 1) -> dict:
        """Get deposit history for a user"""
        deposits = db.query(Deposit).filter(
            Deposit.user_id == user.id
        ).order_by(Deposit.created_at.desc()).offset((page - 1)*limit).limit(limit).all()

        return {
            "deposits": deposits,
            "total": user.deposits_count,
            "total_amount": user.total_deposit_amount,
            "pending_amount": user.total_pending_deposit_amount
        }

    @staticmethod
    def get_deposit_by_id(db: Session, user: User, deposit_id: int) -> DepositResponse:
        """Get a specific deposit by ID"""
        deposit = db.query(Deposit).filter(
            Deposit.id == deposit_id,
            Deposit.user_id == user.id
        ).first()

        if not deposit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deposit not found"
            )

        return DepositResponse.model_validate(deposit)

    @staticmethod
    def get_deposit_stats(db: Session, user: User) -> DepositStatsResponse:
        """Get deposit statistics for a user"""

        total_deposits = len(user.deposits)
        total_amount = user.total_deposit_amount
        total_pending_amount = user.total_pending_deposit_amount
        total_withdrawals_amount = user.total_withdrawal_amount
        completed_deposits = user.completed_deposits_count
        pending_deposits = user.pending_deposits_count
        failed_deposits = user.failed_deposits_count
        completed_withdrawals = len(user.completed_withdrawals)
        average_amount = total_amount / completed_deposits if completed_deposits > 0 else 0

        return DepositStatsResponse(
            total_deposits=total_deposits,
            total_amount=total_amount,
            total_pending_amount=total_pending_amount,
            total_withdrawals_amount=total_withdrawals_amount,
            completed_deposits=completed_deposits,
            pending_deposits=pending_deposits,
            failed_deposits=failed_deposits,
            completed_withdrawals=completed_withdrawals,
            average_amount=average_amount
        )
