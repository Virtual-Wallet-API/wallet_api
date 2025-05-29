import logging
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.deposit import Deposit
from app.models.user import User
from app.schemas.deposit import (
    DepositResponse,
    DepositStatsResponse, DepositPublicResponse
)
from app.schemas.router import UserDepositsFilter

logger = logging.getLogger(__name__)


class DepositService:
    """Business logic for core deposit management"""

    @staticmethod
    def get_user_deposits(db: Session, user: User, search_queries=UserDepositsFilter) -> dict:
        """Get deposit history for a user"""
        search_by = search_queries.search_by
        search_query = search_queries.search_query
        order_by = search_queries.order_by
        limit = search_queries.limit
        page = search_queries.page
        if order_by not in ("asc", "desc"): order_by = "desc"
        offset = (page - 1) * limit

        query = db.query(Deposit).filter(Deposit.user_id == user.id)

        if not search_by or not search_query:
            query = query.order_by(Deposit.created_at.desc()).offset(offset).limit(limit)
        else:
            if search_by == "date_period":
                date_from, date_to = search_query.split("_")
                date_from, date_to = datetime.strptime(date_from, "%Y-%m-%d"), datetime.strptime(date_to, "%Y-%m-%d")

                if date_from > date_to:
                    date_from, date_to = date_to, date_from

                query = (query.filter(Deposit.created_at.between(date_from, date_to)))

            elif search_by == "amount_range":
                amounts = search_query.split("_")
                try:
                    amount_from = float(amounts[0]); amount_to = float(amounts[1])
                except ValueError:
                    pass

            elif search_by == "status" and status in ("failed", "pending", "completed"):
                query = query.filter(Deposit.status == status).offset(offset).limit(limit)

            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid search filter provided: {search_by}")

        deposits = query.all()

        return {
            "deposits": [DepositPublicResponse.model_valudate(DepositResponse) for deposit in deposits],
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
