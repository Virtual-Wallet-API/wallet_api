import logging
from typing import Dict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.business.stripe import *
from app.models import User
from app.models.card import Card
from app.schemas.card import (
    CardUpdate, CardResponse, CardListResponse
)

logger = logging.getLogger(__name__)


class CardService:
    """Business logic for core cards management"""

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
    def validate_card_fingerprint(db: Session, user: User, fingerprint: str) -> Card | bool:
        card = db.query(Card).filter(Card.stripe_card_fingerprint == fingerprint).first()
        if card:
            if card.user_id != user.id:
                return card
            return True
        return False

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
        card = db.query(Card).filter(Card.id == card_id,
                                     Card.user_id == user.id,
                                     Card.is_active == True).first()

        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Card not found")

        # Update fields
        if card_update.cardholder_name is not None:
            card.cardholder_name = card_update.cardholder_name

        if card_update.design is not None:
            # card.design = card_update.design
            # Designs can't be updated
            pass

        if card_update.is_default is not None and card_update.is_default:
            # Remove default from other cards
            dcard = db.query(Card).filter(Card.user_id == user.id, Card.is_default == True).first()
            if dcard:
                dcard.is_default = False

            card.is_default = True

        db.commit()
        db.refresh(card)

        return CardResponse.model_validate(card)

    @staticmethod
    async def delete_card(db: Session, user: User, card_id: int) -> Dict[str, str]:
        """Delete/deactivate a card"""
        card = db.query(Card).filter(
            Card.id == card_id,
            Card.user_id == user.id
        ).first()

        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid card ID provided"
            )

        try:
            # Detach payment method from Stripe
            await StripeService.detach_payment_method(card.stripe_payment_method_id)
        except Exception as e:
            pass

        try:
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

            card.is_default = False

            db.commit()

            logger.info(f"Deleted card {card_id} for user {user.id}")

            return {"message": "Card deleted successfully"}

        except Exception as e:
            logger.error(f"Failed to delete card {card_id} for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete card"
            )
