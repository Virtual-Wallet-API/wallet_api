from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from datetime import datetime

from app.models.withdrawal import Withdrawal
from app.models.card import Card
from app.models.user import User
from app.models.currency import Currency
from app.schemas.withdrawal import (
    WithdrawalCreate, WithdrawalUpdate, WithdrawalResponse,
    WithdrawalPublicResponse, WithdrawalHistoryResponse, WithdrawalStatsResponse,
    RefundCreate, RefundResponse
)
from app.infrestructure.stripe_service import StripeService

logger = logging.getLogger(__name__)


class WithdrawalService:
    """Business logic for withdrawal management with comprehensive tracking"""

    @staticmethod
    async def create_withdrawal(
            db: Session,
            user: User,
            withdrawal_request: WithdrawalCreate
    ) -> WithdrawalResponse:
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
                card = db.query(Card).filter(
                    Card.id == withdrawal_request.card_id,
                    Card.user_id == user.id,
                    Card.is_active == True
                ).first()

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
                status="pending",
                description=withdrawal_request.description,
                estimated_arrival="1-3 business days"
            )

            db.add(withdrawal)
            db.commit()
            db.refresh(withdrawal)

            # Process withdrawal based on type
            if withdrawal_request.withdrawal_type == "payout" and card:
                # For instant payouts (requires Stripe Connect in production)
                withdrawal.status = "processing"
                withdrawal.estimated_arrival = "Instant to 30 minutes"

                # In production, you would create a Stripe payout here
                # payout = await StripeService.create_payout(...)

                # For now, simulate successful processing
                withdrawal.mark_completed()

            elif withdrawal_request.withdrawal_type == "bank_transfer":
                # For bank transfers
                withdrawal.status = "processing"
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
    async def create_refund(
            db: Session,
            user: User,
            refund_request: RefundCreate
    ) -> RefundResponse:
        """Create a refund back to the original payment method with tracking"""
        try:
            # Validate user has sufficient balance for refund
            refund_amount = refund_request.amount_cents / 100  # Convert cents to dollars
            if user.balance < refund_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance for refund"
                )

            # Get currency
            currency = db.query(Currency).filter(Currency.code == "USD").first()
            if not currency:
                currency = Currency(code="USD")
                db.add(currency)
                db.commit()
                db.refresh(currency)

            # Create withdrawal record for tracking
            withdrawal = Withdrawal(
                user_id=user.id,
                currency_id=currency.id,
                amount=refund_amount,
                amount_cents=refund_request.amount_cents,
                withdrawal_type="refund",
                method="card",
                status="pending",
                stripe_payment_intent_id=refund_request.stripe_payment_intent_id,
                description=refund_request.description
            )

            db.add(withdrawal)
            db.commit()
            db.refresh(withdrawal)

            # Create refund through Stripe
            refund = await StripeService.create_refund(
                payment_intent_id=refund_request.stripe_payment_intent_id,
                amount=refund_request.amount_cents,
                reason=refund_request.reason,
                metadata={
                    "user_id": str(user.id),
                    "withdrawal_id": str(withdrawal.id),
                    "description": refund_request.description
                }
            )

            # Update withdrawal record with Stripe refund ID
            withdrawal.stripe_refund_id = refund["id"]
            withdrawal.mark_completed()

            # Update user balance
            user.balance -= refund_amount
            db.commit()
            db.refresh(withdrawal)
            db.refresh(user)

            logger.info(f"Created refund {refund['id']} for user {user.id}, tracked as withdrawal {withdrawal.id}")

            return RefundResponse(
                refund_id=refund["id"],
                amount=refund["amount"],
                currency=refund["currency"],
                status=refund["status"],
                reason=refund["reason"] or refund_request.reason,
                created_at=datetime.fromtimestamp(refund["created"]),
                withdrawal_id=withdrawal.id  # Link to our tracking record
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create refund for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process refund"
            )

    @staticmethod
    def get_user_withdrawals(
            db: Session,
            user: User,
            limit: int = 50,
            status_filter: Optional[str] = None
    ) -> WithdrawalHistoryResponse:
        """Get withdrawal history for a user with filtering"""
        query = db.query(Withdrawal).filter(Withdrawal.user_id == user.id)

        if status_filter:
            query = query.filter(Withdrawal.status == status_filter)

        withdrawals = query.order_by(Withdrawal.created_at.desc()).limit(limit).all()

        withdrawal_responses = []
        for withdrawal in withdrawals:
            card_info = None
            if withdrawal.card:
                card_info = {
                    "id": withdrawal.card.id,
                    "last_four": withdrawal.card.last_four,
                    "brand": withdrawal.card.brand
                }

            withdrawal_dict = {
                "id": withdrawal.id,
                "amount": withdrawal.amount,
                "withdrawal_type": withdrawal.withdrawal_type,
                "method": withdrawal.method,
                "status": withdrawal.status,
                "description": withdrawal.description,
                "estimated_arrival": withdrawal.estimated_arrival,
                "created_at": withdrawal.created_at,
                "completed_at": withdrawal.completed_at,
                "card_info": card_info
            }
            withdrawal_responses.append(WithdrawalPublicResponse(**withdrawal_dict))

        total_amount = sum(w.amount for w in withdrawals if w.is_completed)
        pending_amount = sum(w.amount for w in withdrawals if w.is_pending)

        return WithdrawalHistoryResponse(
            withdrawals=withdrawal_responses,
            total=len(withdrawals),
            total_amount=total_amount,
            pending_amount=pending_amount
        )

    @staticmethod
    def get_withdrawal_by_id(db: Session, user: User, withdrawal_id: int) -> WithdrawalResponse:
        """Get a specific withdrawal by ID"""
        withdrawal = db.query(Withdrawal).filter(
            Withdrawal.id == withdrawal_id,
            Withdrawal.user_id == user.id
        ).first()

        if not withdrawal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Withdrawal not found"
            )

        return WithdrawalResponse.model_validate(withdrawal)

    @staticmethod
    def update_withdrawal_status(
            db: Session,
            user: User,
            withdrawal_id: int,
            update_data: WithdrawalUpdate
    ) -> WithdrawalResponse:
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

            if update_data.status == "completed" and not withdrawal.completed_at:
                withdrawal.completed_at = datetime.utcnow()
            elif update_data.status == "failed" and not withdrawal.failed_at:
                withdrawal.failed_at = datetime.utcnow()

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
        withdrawals = db.query(Withdrawal).filter(Withdrawal.user_id == user.id).all()

        total_withdrawals = len(withdrawals)
        total_amount = sum(w.amount for w in withdrawals if w.is_completed)
        completed_withdrawals = len([w for w in withdrawals if w.is_completed])
        pending_withdrawals = len([w for w in withdrawals if w.is_pending])
        failed_withdrawals = len([w for w in withdrawals if w.status == "failed"])

        # Calculate by type
        refunds = [w for w in withdrawals if w.withdrawal_type == "refund"]
        payouts = [w for w in withdrawals if w.withdrawal_type == "payout"]

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
            payout_amount=sum(p.amount for p in payouts if p.is_completed)
        )

    @staticmethod
    def cancel_withdrawal(db: Session, user: User, withdrawal_id: int) -> WithdrawalResponse:
        """Cancel a pending withdrawal"""
        withdrawal = db.query(Withdrawal).filter(
            Withdrawal.id == withdrawal_id,
            Withdrawal.user_id == user.id
        ).first()

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
        withdrawal.status = "cancelled"
        user.balance += withdrawal.amount  # Refund the amount

        db.commit()
        db.refresh(withdrawal)
        db.refresh(user)

        logger.info(f"Cancelled withdrawal {withdrawal_id} for user {user.id}, refunded ${withdrawal.amount}")

        return WithdrawalResponse.model_validate(withdrawal) 