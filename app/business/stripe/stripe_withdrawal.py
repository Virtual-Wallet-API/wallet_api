import logging
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.business.stripe.stripe_service import StripeService
from app.models.currency import Currency
from app.models.user import User
from app.models.withdrawal import Withdrawal
from app.schemas.withdrawal import (
    RefundCreate, RefundResponse
)

logger = logging.getLogger(__name__)


class StripeWithdrawalService:
    """Business logic for withdrawal management with Stripe integration"""

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
