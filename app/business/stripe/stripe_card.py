import logging
import traceback
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.business.payment.payment_card import CardService
from app.business.stripe import StripeService
from app.business.user import UAuth
from app.business.utils.pattern_generator import PatternGenerator
from app.models import User, Card
from app.models.card_design import CardDesign
from app.schemas.card import PaymentIntentResponse, PaymentIntentCreate, SetupIntentResponse

logger = logging.getLogger(__name__)


class StripeCardService:
    """Business logic for card management with Stripe integration"""

    @staticmethod
    async def ensure_stripe_customer(db: Session, user: User) -> str:
        """
        Ensures that a Stripe customer is associated with the given user. If the user
        does not already have an associated Stripe customer ID, a new Stripe customer
        is created using the provided user details. Once the customer is created, the
        Stripe customer ID is stored in the user's record and persisted in the database.

        :param db: Instance of the database session used to commit and refresh the user
            record after it is updated with the Stripe customer ID.
        :param user: The user object whose Stripe customer ID is to be ensured or
            created. This user object must have attributes for email, username, and id.
        :return: The Stripe customer ID associated with the user, either previously
            existing or newly created.
        """
        if not user.stripe_customer_id:
            try:
                stripe_customer = await StripeService.create_customer(email=user.email,
                                                                      name=user.username,
                                                                      metadata={"user_id": str(user.id)})

                user.stripe_customer_id = stripe_customer["id"]
                db.commit()
                db.refresh(user)

                logger.info(f"Created Stripe customer {stripe_customer['id']} for user {user.id}")

            except Exception as e:
                logger.error(f"Failed to create Stripe customer for user {user.id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Failed to create payment customer [{e}]")

        return user.stripe_customer_id

    @staticmethod
    async def create_setup_intent(db: Session, user: User) -> SetupIntentResponse:
        """Create a setup intent for saving a payment method"""
        UAuth.verify_user_can_add_card(user)
        try:
            # Ensure user has Stripe customer
            stripe_customer_id = await StripeCardService.ensure_stripe_customer(db, user)

            # Create setup intent
            setup_intent = await StripeService.create_setup_intent(
                customer_id=stripe_customer_id,
                usage="off_session",
                metadata={"user_id": str(user.id)}
            )

            return SetupIntentResponse(
                client_secret=setup_intent["client_secret"],
                setup_intent_id=setup_intent["id"],
                status=setup_intent["status"]
            )

        except Exception as e:
            logger.error(f"Failed to create setup intent for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create card setup"
            )

    @staticmethod
    async def create_payment_intent(
            db: Session,
            user: User,
            payment_data: PaymentIntentCreate
    ) -> PaymentIntentResponse:
        """Create a payment intent for processing a payment"""
        UAuth.verify_user_can_deposit(user)
        try:
            # Ensure user has Stripe customer
            stripe_customer_id = await StripeCardService.ensure_stripe_customer(db, user)

            # Create payment intent
            payment_intent = await StripeService.create_payment_intent(
                amount=payment_data.amount,
                currency=payment_data.currency,
                customer_id=stripe_customer_id,
                metadata={
                    "user_id": str(user.id),
                    "description": payment_data.description or "Wallet deposit"
                },
                setup_future_usage="off_session" if payment_data.save_payment_method else None
            )

            return PaymentIntentResponse(
                client_secret=payment_intent["client_secret"],
                payment_intent_id=payment_intent["client_secret"],
                amount=payment_intent["amount"],
                currency=payment_intent["currency"],
                status=payment_intent["status"]
            )

        except Exception as e:
            logger.error(f"Failed to create payment intent for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment"
            )

    @staticmethod
    async def save_card_from_payment_method(
            db: Session,
            user: User,
            payment_method_id: str,
            cardholder_name: Optional[str] = None
    ) -> Card:
        """Save a card to database after successful Stripe payment method creation"""
        UAuth.verify_user_can_add_card(user)
        # Retrieve payment method from Stripe
        payment_method = await StripeService.retrieve_payment_method(payment_method_id)
        if payment_method["type"] != "card":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only card payment methods are supported"
            )

        card_fingerprint = payment_method["card"]["fingerprint"]
        existing = CardService.validate_card_fingerprint(db, user, card_fingerprint)
        if type(existing) == type(Card):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Card is already associated with another account"
            )

        if not existing:
            # Determine if this should be the default card
            is_default = db.query(Card).filter(Card.user_id == user.id).count() == 0

            # Create card record
            card_data = payment_method["card"]
            card = Card(
                user_id=user.id,
                stripe_payment_method_id=payment_method_id,
                stripe_customer_id=user.stripe_customer_id,
                stripe_card_fingerprint=card_fingerprint,
                last_four=card_data["last4"],
                brand=card_data["brand"],
                exp_month=card_data["exp_month"],
                exp_year=card_data["exp_year"],
                cardholder_name=cardholder_name or f"{user.username}",
                type="unknown",  # Stripe doesn't provide funding type in all cases
                is_default=is_default,
                is_active=True
            )

            db.add(card)
            try:
                db.commit()
                db.refresh(card)
                design = PatternGenerator.generate_pattern(int(card.last_four) + card.id)
                design["card_id"] = card.id
                design_db = CardDesign(**design)
                db.add(design_db)
                db.commit()
                db.refresh(design_db)
                card.design_id = design_db.id
                db.commit()
                db.refresh(card)
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to save card for user {user.id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save card: {e}"
                )

            logger.info(f"Saved card {card.id} for user {user.id}")

            return card
        else:
            raise HTTPException(status_code=400, detail="Card is already saved in our system.")
