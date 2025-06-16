import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import WStatus, WType
from app.models.currency import Currency
from app.models.user import User
from app.models.withdrawal import Withdrawal
from app.schemas.withdrawal import (
    WithdrawalCreate, WithdrawalUpdate, WithdrawalResponse,
    WithdrawalPublicResponse, WithdrawalHistoryResponse, WithdrawalStatsResponse
)

logger = logging.getLogger(__name__)


class WithdrawalService:
    """Business logic for withdrawal management with comprehensive tracking"""

    @staticmethod
    async def create_withdrawal(db: Session,
                                user: User,
                                withdrawal_request: WithdrawalCreate) -> WithdrawalResponse:
        """Create a new withdrawal with proper tracking"""
        try:
            # Validate user has sufficient balance
            withdrawal_amount = withdrawal_request.amount_cents / 100  # Convert cents to dollars
            if user.balance < withdrawal_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance for withdrawal"
                )

            # Get the card if specified
            card = None
            if withdrawal_request.card_id:
                # card = db.query(Card).filter(
                #     Card.id == withdrawal_request.card_id,
                #     Card.user_id == user.id,
                #     Card.is_active == True
                # ).first()
                card = next((c for c in user.cards if c.id == withdrawal_request.card_id and c.is_active), None)

                if not card:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Card not found"
                    )

                if card.is_expired:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot withdraw to expired card"
                    )

            # Get currency
            currency = db.query(Currency).filter(Currency.code == withdrawal_request.currency_code).first()
            if not currency:
                currency = Currency(code=withdrawal_request.currency_code)
                db.add(currency)
                db.commit()
                db.refresh(currency)

            # Create withdrawal record with comprehensive tracking
            withdrawal = Withdrawal(
                user_id=user.id,
                card_id=card.id if card else None,
                currency_id=currency.id,
                amount=withdrawal_amount,
                amount_cents=withdrawal_request.amount_cents,
                withdrawal_type=withdrawal_request.withdrawal_type,
                method=withdrawal_request.method,
                status=WStatus.PENDING,
                description=withdrawal_request.description,
                estimated_arrival="1-3 business days"
            )

            db.add(withdrawal)
            db.commit()
            db.refresh(withdrawal)

            # Process withdrawal based on type
            if withdrawal_request.withdrawal_type == WType.PAYOUT and card:
                # For instant payouts (requires Stripe Connect in production)
                withdrawal.status = WStatus.PROCESSING
                withdrawal.estimated_arrival = "Instant to 30 minutes"

                # In production, you would create a Stripe payout here
                # payout = await StripeService.create_payout(...)

                # For now, simulate successful processing
                withdrawal.mark_completed()

            elif withdrawal_request.withdrawal_type == "bank_transfer":
                # For bank transfers
                withdrawal.status = WStatus.PROCESSING
                withdrawal.estimated_arrival = "3-5 business days"

                # Simulate bank transfer processing
                withdrawal.mark_completed()

            # Update user balance
            user.balance -= withdrawal_amount
            db.commit()
            db.refresh(withdrawal)
            db.refresh(user)

            logger.info(f"Created withdrawal {withdrawal.id} for user {user.id}, amount: ${withdrawal_amount}")

            return WithdrawalResponse.model_validate(withdrawal)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create withdrawal for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process withdrawal"
            )

    @staticmethod
    def get_user_withdrawals(db: Session,
                             user: User,
                             limit: int = 30,
                             status_filter: Optional[str] = None) -> WithdrawalHistoryResponse:
        """Get withdrawal history for a user with filtering"""
        filtered_withdrawals = []
        if status_filter:
            filtered_withdrawals = [w for w in user.withdrawals
                                    if w.status == status_filter]

        # withdrawals = user.withdrawals[:limit] if not status_filter else filtered_withdrawals[:limit]
        wquery = db.query(Withdrawal).filter(Withdrawal.user_id == user.id).order_by(Withdrawal.created_at.desc())
        withdrawals = wquery.limit(limit).all()
        total_count = wquery.count()

        withdrawal_responses = [WithdrawalPublicResponse.model_validate(w) for w in withdrawals]

        found_total = len(withdrawals)
        total_amount = user.total_withdrawal_amount
        found_amount = sum([w.amount for w in withdrawals])
        pending_amount = user.total_pending_withdrawal_amount

        return WithdrawalHistoryResponse(
            withdrawals=withdrawal_responses,
            total=total_count,
            found_total=found_total,
            total_amount=total_amount,
            found_amount=found_amount,
            pending_amount=pending_amount
        )

    @staticmethod
    def get_withdrawal_by_id(db: Session, user: User, withdrawal_id: int) -> WithdrawalResponse:
        """Get a specific withdrawal by ID"""
        # withdrawal = db.query(Withdrawal).filter(
        #     Withdrawal.id == withdrawal_id,
        #     Withdrawal.user_id == user.id
        # ).first()
        withdrawal = next((w for w in user.withdrawals
                           if w.id == withdrawal_id), None)

        if not withdrawal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Withdrawal not found"
            )

        return WithdrawalResponse.model_validate(withdrawal)

    @staticmethod
    def update_withdrawal_status(db: Session,
                                 user: User,
                                 withdrawal_id: int,
                                 update_data: WithdrawalUpdate) -> WithdrawalResponse:
        """Update withdrawal status (admin function)"""
        withdrawal = db.query(Withdrawal).filter(
            Withdrawal.id == withdrawal_id,
            Withdrawal.user_id == user.id
        ).first()

        if not withdrawal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Withdrawal not found"
            )

        # Update fields
        if update_data.status:
            withdrawal.status = update_data.status

            if update_data.status == WStatus.COMPLETED and not withdrawal.completed_at:
                withdrawal.completed_at = datetime.now()
            elif update_data.status == WStatus.FAILED and not withdrawal.failed_at:
                withdrawal.failed_at = datetime.now()

        if update_data.failure_reason:
            withdrawal.failure_reason = update_data.failure_reason

        if update_data.stripe_payout_id:
            withdrawal.stripe_payout_id = update_data.stripe_payout_id

        if update_data.estimated_arrival:
            withdrawal.estimated_arrival = update_data.estimated_arrival

        db.commit()
        db.refresh(withdrawal)

        return WithdrawalResponse.model_validate(withdrawal)

    @staticmethod
    def get_withdrawal_stats(db: Session, user: User) -> WithdrawalStatsResponse:
        """Get withdrawal statistics for a user"""

        total_withdrawals = len(user.withdrawals)
        total_amount = user.total_withdrawal_amount
        completed_withdrawals = len(user.completed_withdrawals)
        pending_withdrawals = len(user.pending_withdrawals)
        failed_withdrawals = len(user.failed_withdrawals)

        # Calculate by type
        refunds = user.refunds
        payouts = user.payouts

        average_amount = total_amount / completed_withdrawals if completed_withdrawals > 0 else 0

        return WithdrawalStatsResponse(
            total_withdrawals=total_withdrawals,
            total_amount=total_amount,
            completed_withdrawals=completed_withdrawals,
            pending_withdrawals=pending_withdrawals,
            failed_withdrawals=failed_withdrawals,
            average_amount=average_amount,
            total_refunds=len(refunds),
            total_payouts=len(payouts),
            refund_amount=sum(r.amount for r in refunds if r.is_completed),
            payout_amount=sum(p.amount for p in payouts if p.is_completed),
            total_lasts_month=user.total_withdrawals_last_month,
            total_amount_last_month=user.total_withdrawn_amount_last_month,
            withdraw_frequency=user.withdrawal_frequency,
            average_last_month=user.average_last_month
        )

    @staticmethod
    def cancel_withdrawal(db: Session, user: User, withdrawal_id: int) -> WithdrawalResponse:
        """Cancel a pending withdrawal"""
        withdrawal = next((w for w in user.withdrawals
                           if w.id == withdrawal_id and w.status == WStatus.PENDING), None)

        if not withdrawal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Withdrawal not found"
            )

        if not withdrawal.can_be_cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Withdrawal cannot be cancelled"
            )

        # Cancel withdrawal and refund balance
        withdrawal.status = WStatus.CANCELLED
        user.balance += withdrawal.amount  # Refund the amount

        db.commit()
        db.refresh(withdrawal)
        db.refresh(user)

        logger.info(f"Cancelled withdrawal {withdrawal_id} for user {user.id}, refunded ${withdrawal.amount}")

        return WithdrawalResponse.model_validate(withdrawal)
