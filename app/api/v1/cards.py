from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.business import StripeCardService, CardService
from app.config import STRIPE_PUBLISHABLE_KEY
from app.dependencies import get_db, get_user_except_fpr
from app.models.user import User
from app.schemas.card import (
    CardResponse, CardUpdate, CardListResponse,
    PaymentIntentCreate, PaymentIntentResponse, SetupIntentResponse, AddCard
)

router = APIRouter(tags=["Cards"])


@router.get("/config")
def get_stripe_config(user: User = Depends(get_user_except_fpr), db: Session = Depends(get_db)):
    """Get Stripe configuration for frontend"""
    return {
        "publishable_key": STRIPE_PUBLISHABLE_KEY
    }


@router.post("/setup-intent", response_model=SetupIntentResponse)
async def create_setup_intent(
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Create a setup intent for saving a payment method without charging"""
    return await StripeCardService.create_setup_intent(db, user)


@router.post("/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
        payment_data: PaymentIntentCreate,
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Create a payment intent for processing a payment"""
    return await StripeCardService.create_payment_intent(db, user, payment_data)


@router.post("/save-payment-method", response_model=CardResponse)
async def save_payment_method(
        card_data: AddCard,
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Save a payment method as a card after successful setup"""
    return await StripeCardService.save_card_from_payment_method(
        db, user, **card_data.model_dump()
    )


@router.get("/", response_model=CardListResponse)
def get_user_cards(
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Get all cards for the current user"""
    return CardService.get_user_cards(db, user)


@router.get("/user-cards", response_model=None)
def get_user_cards_with_design(db: Session = Depends(get_db),
                               user: User = Depends(get_user_except_fpr)):
    """
    Get all cards belonging to the authenticated user with design information
    """
    cards_with_design = []
    for card in user.cards:
        card_data = {
            "id": card.id,
            "last_four": card.last_four,
            "brand": card.brand,
            "exp_month": card.exp_month,
            "exp_year": card.exp_year,
            "cardholder_name": card.cardholder_name,
            "type": card.type,
            "is_default": card.is_default,
            "is_active": card.is_active,
            "created_at": card.created_at,
            "masked_number": card.masked_number,
            "design": None
        }
        
        if card.design:
            card_data["design"] = {
                "pattern": card.design.pattern,
                "color": card.design.color,
                "params": card.design.params
            }
        
        cards_with_design.append(card_data)
    
    return cards_with_design


@router.get("/{card_id}", response_model=CardResponse)
def get_card(
        card_id: int,
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Get a specific card by ID"""
    return CardService.get_card_by_id(db, user, card_id)


@router.patch("/{card_id}", response_model=CardResponse)
def update_card(
        card_id: int,
        card_update: CardUpdate,
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Update card information - design only for now"""
    # TODO
    return CardService.update_card(db, user, card_id, card_update)


@router.patch("/{card_id}/customize", response_model=None)
def customize_card(card_id: int,
                   customization_data: dict,
                   db: Session = Depends(get_db),
                   user: User = Depends(get_user_except_fpr)):
    """
    Customize card appearance (color, theme, pattern)
    """
    from app.models.card_design import CardDesign, DesignPatterns
    from app.models.card import Card
    import json
    
    # Find the card
    card = db.query(Card).filter(
        Card.id == card_id,
        Card.user_id == user.id
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Get or create card design
    design = card.design
    if not design:
        design = CardDesign(
            card_id=card.id,
            pattern=DesignPatterns.GRID,
            color=customization_data.get("color", "#667eea"),
            params="{}"
        )
        db.add(design)
    else:
        # Update existing design
        if "color" in customization_data:
            design.color = customization_data["color"]
        if "theme" in customization_data:
            # Store theme information in params
            params = json.loads(design.params) if design.params else {}
            params["theme"] = customization_data["theme"]
            design.params = json.dumps(params)
    
    try:
        db.commit()
        db.refresh(design)
        return {"message": "Card customization updated successfully", "design": design}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update card customization")


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
        card_id: int,
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Delete/deactivate a card"""
    try:
        remove = await CardService.delete_card(db, user, card_id)
        return remove
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{card_id}/default", response_model=CardResponse)
def set_default_card(
        card_id: int,
        user: User = Depends(get_user_except_fpr),
        db: Session = Depends(get_db)
):
    """Set a card as the default payment method"""
    card_update = CardUpdate(is_default=True)
    return CardService.update_card(db, user, card_id, card_update)


@router.post("/", response_model=CardResponse)
async def add_card(
    card_data: AddCard,
    user: User = Depends(get_user_except_fpr),
    db: Session = Depends(get_db)
):
    return await StripeCardService.save_card_from_payment_method(db, user, **card_data.model_dump())
