from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.card import (
    CardResponse, CardUpdate, CardPublicResponse, CardListResponse,
    PaymentIntentCreate, PaymentIntentResponse, SetupIntentResponse,
    CardDelete
)

from app.business.card_service import CardService
from app.config import STRIPE_PUBLISHABLE_KEY

router = APIRouter(tags=["Cards"])

@router.get("/config")
def get_stripe_config(user: User = Depends(get_current_active_user)):
    """Get Stripe configuration for frontend"""
    return {
        "publishable_key": STRIPE_PUBLISHABLE_KEY
    }

@router.post("/setup-intent", response_model=SetupIntentResponse)
async def create_setup_intent(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a setup intent for saving a payment method without charging"""
    return await CardService.create_setup_intent(db, user)

@router.post("/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a payment intent for processing a payment"""
    return await CardService.create_payment_intent(db, user, payment_data)

@router.post("/save-payment-method", response_model=CardResponse)
async def save_payment_method(
    payment_method_id: str,
    cardholder_name: str = None,
    design: str = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save a payment method as a card after successful setup"""
    return await CardService.save_card_from_payment_method(
        db, user, payment_method_id, cardholder_name, design
    )

@router.get("/", response_model=CardListResponse)
def get_user_cards(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all cards for the current user"""
    return CardService.get_user_cards(db, user)

@router.get("/{card_id}", response_model=CardResponse)
def get_card(
    card_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific card by ID"""
    return CardService.get_card_by_id(db, user, card_id)

@router.put("/{card_id}", response_model=CardResponse)
def update_card(
    card_id: int,
    card_update: CardUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update card information"""
    return CardService.update_card(db, user, card_id, card_update)

@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete/deactivate a card"""
    try:
        remove = await CardService.delete_card(db, user, card_id)
        return remove
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{card_id}/set-default", response_model=CardResponse)
def set_default_card(
    card_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Set a card as the default payment method"""
    card_update = CardUpdate(is_default=True)
    return CardService.update_card(db, user, card_id, card_update)


