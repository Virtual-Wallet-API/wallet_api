from typing import Optional, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.models.card import Card
from app.models.user import User

from app.schemas.card import (
    CardUpdate, CardResponse, CardPublicResponse,
    PaymentIntentCreate, PaymentIntentResponse, SetupIntentResponse,
    CardListResponse
)

from app.infrestructure.stripe_service import StripeService

logger = logging.getLogger(__name__)


class CardService:
    """Business logic for card management with Stripe integration"""

    @staticmethod
    async def ensure_stripe_customer(db: Session, user: User) -> str:
        """Ensure user has a Stripe customer ID, create one if not"""
        if not user.stripe_customer_id:
            try:
                # Create Stripe customer
                stripe_customer = await StripeService.create_customer(
                    email=user.email,
                    name=user.username,
                    metadata={"user_id": str(user.id)}
                )

                # Update user with Stripe customer ID
                user.stripe_customer_id = stripe_customer["id"]
                db.commit()
                db.refresh(user)

                logger.info(f"Created Stripe customer {stripe_customer['id']} for user {user.id}")

            except Exception as e:
                logger.error(f"Failed to create Stripe customer for user {user.id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create payment customer"
                )

        return user.stripe_customer_id

    @staticmethod
    async def create_setup_intent(db: Session, user: User) -> SetupIntentResponse:
        """Create a setup intent for saving a payment method"""
        try:
            # Ensure user has Stripe customer
            stripe_customer_id = await CardService.ensure_stripe_customer(db, user)

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
        try:
            # Ensure user has Stripe customer
            stripe_customer_id = await CardService.ensure_stripe_customer(db, user)

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
            stripe_payment_method_id: str,
            cardholder_name: Optional[str] = None,
            design: Optional[str] = None
    ) -> CardResponse:
        """Save a card to database after successful Stripe payment method creation"""
        try:
            # Retrieve payment method from Stripe
            payment_method = await StripeService.retrieve_payment_method(stripe_payment_method_id)

            if payment_method["type"] != "card":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only card payment methods are supported"
                )

            card_data = payment_method["card"]
            card_fingerprint = card_data["fingerprint"]

            # Check if card already exists
            # TODO: Check for existing card with same fingerprint
            existing_card = db.query(Card).filter(
                Card.stripe_card_fingerprint == card_fingerprint
            ).first()

            if existing_card:
                if existing_card.user_id != user.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This card is already associated with another account"
                    )

            # Determine if this should be the default card
            is_default = db.query(Card).filter(Card.user_id == user.id).count() == 0

            # Create card record
            card = Card(
                user_id=user.id,
                stripe_payment_method_id=stripe_payment_method_id,
                stripe_customer_id=user.stripe_customer_id,
                stripe_card_fingerprint=card_fingerprint,
                last_four=card_data["last4"],
                brand=card_data["brand"],
                exp_month=card_data["exp_month"],
                exp_year=card_data["exp_year"],
                cardholder_name=cardholder_name or f"{user.username}",
                type="unknown",  # Stripe doesn't provide funding type in all cases
                design=design or '{"color": "purple"}',
                is_default=is_default,
                is_active=True
            )

            db.add(card)
            db.commit()
            db.refresh(card)

            logger.info(f"Saved card {card.id} for user {user.id}")

            return CardResponse.model_validate(card)

        except HTTPException:
            raise

    @staticmethod
    def get_user_cards(db: Session, user: User) -> CardListResponse:
        """Get all cards for a user"""
        cards = db.query(Card).filter(
            Card.user_id == user.id,
            Card.is_active == True
        ).order_by(Card.is_default.desc(), Card.created_at.desc()).all()

        card_responses = []
        for card in cards:
            card_dict = {
                "id": card.id,
                "stripe_payment_method_id": card.stripe_payment_method_id,
                "last_four": card.last_four,
                "brand": card.brand,
                "exp_month": card.exp_month,
                "exp_year": card.exp_year,
                "cardholder_name": card.cardholder_name,
                "type": card.type,
                "design": card.design,
                "is_default": card.is_default,
                "is_active": card.is_active,
                "masked_number": card.masked_number,
                "is_expired": card.is_expired,
                "created_at": card.created_at
            }
            card_responses.append(CardResponse(**card_dict))

        has_default = any(card.is_default for card in cards)

        return CardListResponse(
            cards=card_responses,
            total=len(cards),
            has_default=has_default
        )

    @staticmethod
    def get_card_by_id(db: Session, user: User, card_id: int) -> CardResponse:
        """Get a specific card by ID"""
        card = db.query(Card).filter(
            Card.id == card_id,
            Card.user_id == user.id,
            Card.is_active == True
        ).first()

        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )

        return CardResponse.model_validate(card)

    @staticmethod
    def update_card(db: Session, user: User, card_id: int, card_update: CardUpdate) -> CardResponse:
        """Update card information"""
        card = db.query(Card).filter(
            Card.id == card_id,
            Card.user_id == user.id,
            Card.is_active == True
        ).first()

        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )

        # Update fields
        if card_update.cardholder_name is not None:
            card.cardholder_name = card_update.cardholder_name

        if card_update.design is not None:
            card.design = card_update.design

        if card_update.is_default is not None and card_update.is_default:
            # Remove default from other cards
            db.query(Card).filter(
                Card.user_id == user.id,
                Card.id != card_id
            ).update({"is_default": False})
            card.is_default = True

        if card_update.is_active is not None:
            card.is_active = card_update.is_active

        db.commit()
        db.refresh(card)

        return CardResponse.model_validate(card)

    @staticmethod
    async def delete_card(db: Session, user: User, card_id: int) -> Dict[str, str]:
        """Delete/deactivate a card"""
        card = db.query(Card).filter(
            Card.id == card_id,
            Card.user_id == user.id,
            Card.is_active == True
        ).first()

        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )

        try:
            # Detach payment method from Stripe
            await StripeService.detach_payment_method(card.stripe_payment_method_id)

            # Deactivate card in database
            card.is_active = False

            # If this was the default card, make another card default
            if card.is_default:
                other_card = db.query(Card).filter(
                    Card.user_id == user.id,
                    Card.id != card_id,
                    Card.is_active == True
                ).first()

                if other_card:
                    other_card.is_default = True

            db.commit()

            logger.info(f"Deleted card {card_id} for user {user.id}")

            return {"message": "Card deleted successfully"}

        except Exception as e:
            logger.error(f"Failed to delete card {card_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete card"
            )

