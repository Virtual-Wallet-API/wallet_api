from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging
from datetime import datetime

from app.models.deposit import Deposit
from app.models.card import Card
from app.models.user import User
from app.models.currency import Currency
from app.schemas.deposit import (
    DepositCreate, DepositWithCard, DepositUpdate, DepositResponse,
    DepositPublicResponse, DepositHistoryResponse, DepositStatsResponse,
    DepositPaymentIntentCreate, DepositPaymentIntentResponse, DepositConfirm
)
from app.infrestructure.stripe_service import StripeService
from app.business.card_service import CardService

logger = logging.getLogger(__name__)


class DepositService:
    """Business logic for deposit management with Stripe integration"""

    @staticmethod
    async def create_deposit_payment_intent(
            db: Session,
            user: User,
            deposit_data: DepositPaymentIntentCreate
    ) -> DepositPaymentIntentResponse:
        """Create a payment intent for a new deposit (with new card)"""
        try:
            # Ensure user has Stripe customer
            stripe_customer_id = await CardService.ensure_stripe_customer(db, user)

            # Get or create USD currency
            currency = db.query(Currency).filter(Currency.code == "USD").first()
            if not currency:
                currency = Currency(code="USD")
                db.add(currency)
                db.commit()
                db.refresh(currency)

            # Create deposit record first
            deposit = Deposit(
                user_id=user.id,
                currency_id=currency.id,
                amount=deposit_data.amount_cents / 100,  # Convert cents to dollars
                amount_cents=deposit_data.amount_cents,
                deposit_type="card_payment",
                method="stripe",
                status="pending",
                description=deposit_data.description
            )

            db.add(deposit)
            db.commit()
            db.refresh(deposit)

            # Create payment intent with Stripe
            payment_intent = await StripeService.create_payment_intent(
                amount=deposit_data.amount_cents,
                currency=deposit_data.currency,
                customer_id=stripe_customer_id,
                metadata={
                    "user_id": str(user.id),
                    "deposit_id": str(deposit.id),
                    "description": deposit_data.description or "Wallet deposit"
                },
                setup_future_usage="off_session" if deposit_data.save_payment_method else None
            )

            # Update deposit with Stripe payment intent ID
            deposit.stripe_payment_intent_id = payment_intent["id"]
            deposit.stripe_customer_id = stripe_customer_id
            db.commit()
            db.refresh(deposit)

            logger.info(f"Created deposit payment intent {payment_intent['id']} for user {user.id}")

            return DepositPaymentIntentResponse(
                client_secret=payment_intent["client_secret"],
                payment_intent_id=payment_intent["id"],
                amount=payment_intent["amount"],
                currency=payment_intent["currency"],
                status=payment_intent["status"],
                deposit_id=deposit.id
            )

        except Exception as e:
            logger.error(f"Failed to create deposit payment intent for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create deposit payment intent"
            )

    @staticmethod
    async def deposit_with_existing_card(
            db: Session,
            user: User,
            deposit_data: DepositWithCard
    ) -> DepositPaymentIntentResponse:
        """Create a deposit using an existing saved card"""
        try:
            # Get the card
            card = db.query(Card).filter(
                Card.id == deposit_data.card_id,
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
                    detail="Cannot use expired card"
                )

            # Get currency
            currency = db.query(Currency).filter(Currency.code == deposit_data.currency_code).first()
            if not currency:
                currency = Currency(code=deposit_data.currency_code)
                db.add(currency)
                db.commit()
                db.refresh(currency)

            # Create deposit record
            deposit = Deposit(
                user_id=user.id,
                card_id=card.id,
                currency_id=currency.id,
                amount=deposit_data.amount_cents / 100,
                amount_cents=deposit_data.amount_cents,
                deposit_type="card_payment",
                method="stripe",
                status="pending",
                description=deposit_data.description
            )

            db.add(deposit)
            db.commit()
            db.refresh(deposit)

            # Create payment intent with existing payment method
            payment_intent = await StripeService.create_payment_intent(
                amount=deposit_data.amount_cents,
                currency=deposit_data.currency_code.lower(),
                customer_id=user.stripe_customer_id,
                metadata={
                    "user_id": str(user.id),
                    "deposit_id": str(deposit.id),
                    "card_id": str(card.id),
                    "description": deposit_data.description or "Wallet deposit"
                }
            )

            # Confirm payment intent with saved payment method
            confirmed_payment = await StripeService.confirm_payment_intent(
                payment_intent["id"],
                card.stripe_payment_method_id
            )

            # Update deposit with Stripe info
            deposit.stripe_payment_intent_id = confirmed_payment["id"]
            deposit.stripe_customer_id = user.stripe_customer_id
            deposit.status = "processing"
            db.commit()
            db.refresh(deposit)

            logger.info(f"Created deposit with existing card {card.id} for user {user.id}")

            return DepositPaymentIntentResponse(
                client_secret=confirmed_payment["client_secret"],
                payment_intent_id=confirmed_payment["id"],
                amount=confirmed_payment["amount"],
                currency=confirmed_payment["currency"],
                status=confirmed_payment["status"],
                deposit_id=deposit.id
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create deposit with existing card for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process deposit"
            )

    @staticmethod
    async def confirm_deposit(
            db: Session,
            user: User,
            confirm_data: DepositConfirm
    ) -> DepositResponse:
        """Confirm a deposit and update user balance"""
        try:
            # Get the deposit by payment intent ID
            deposit = db.query(Deposit).filter(
                Deposit.stripe_payment_intent_id == confirm_data.payment_intent_id,
                Deposit.user_id == user.id
            ).first()

            if not deposit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Deposit not found"
                )

            # Retrieve payment intent from Stripe to check status
            payment_intent = await StripeService.retrieve_payment_intent(confirm_data.payment_intent_id)

            if payment_intent["status"] == "succeeded":
                # Update deposit status
                deposit.mark_completed()

                # Update user balance
                user.balance += deposit.amount

                # Save card if requested and payment method exists
                if confirm_data.save_card and payment_intent.get("payment_method"):
                    try:
                        await CardService.save_card_from_payment_method(
                            db, user, payment_intent["payment_method"],
                            confirm_data.cardholder_name
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save card for user {user.id}: {e}")

                # Update Stripe charge ID if available
                if payment_intent.get("charges", {}).get("data"):
                    charge = payment_intent["charges"]["data"][0]
                    deposit.stripe_charge_id = charge["id"]

                db.commit()
                db.refresh(deposit)
                db.refresh(user)

                logger.info(f"Confirmed deposit {deposit.id} for user {user.id}, new balance: ${user.balance}")

            elif payment_intent["status"] == "requires_action":
                deposit.status = "processing"
                db.commit()
                db.refresh(deposit)

            elif payment_intent["status"] in ["canceled", "payment_failed"]:
                deposit.mark_failed("Payment failed or was canceled")
                db.commit()
                db.refresh(deposit)

            return DepositResponse.model_validate(deposit)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to confirm deposit for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to confirm deposit"
            )

    @staticmethod
    def get_user_deposits(db: Session, user: User, limit: int = 50) -> DepositHistoryResponse:
        """Get deposit history for a user"""
        deposits = db.query(Deposit).filter(
            Deposit.user_id == user.id
        ).order_by(Deposit.created_at.desc()).limit(limit).all()

        deposit_responses = []
        for deposit in deposits:
            card_last_four = None
            if deposit.card:
                card_last_four = deposit.card.last_four

            deposit_dict = {
                "id": deposit.id,
                "amount": deposit.amount,
                "deposit_type": deposit.deposit_type,
                "method": deposit.method,
                "status": deposit.status,
                "description": deposit.description,
                "created_at": deposit.created_at,
                "completed_at": deposit.completed_at,
                "card_last_four": card_last_four
            }
            deposit_responses.append(DepositPublicResponse(**deposit_dict))

        total_amount = sum(d.amount for d in deposits if d.is_completed)
        pending_amount = sum(d.amount for d in deposits if d.is_pending)

        return DepositHistoryResponse(
            deposits=deposit_responses,
            total=len(deposits),
            total_amount=total_amount,
            pending_amount=pending_amount
        )

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
        deposits = db.query(Deposit).filter(Deposit.user_id == user.id).all()

        total_deposits = len(deposits)
        total_amount = sum(d.amount for d in deposits if d.is_completed)
        completed_deposits = len([d for d in deposits if d.is_completed])
        pending_deposits = len([d for d in deposits if d.is_pending])
        failed_deposits = len([d for d in deposits if d.status == "failed"])
        average_amount = total_amount / completed_deposits if completed_deposits > 0 else 0

        return DepositStatsResponse(
            total_deposits=total_deposits,
            total_amount=total_amount,
            completed_deposits=completed_deposits,
            pending_deposits=pending_deposits,
            failed_deposits=failed_deposits,
            average_amount=average_amount
        ) 