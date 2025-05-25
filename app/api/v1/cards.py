from datetime import datetime, timedelta
from random import randint
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models import Card, User
from app.schemas.card import CardResponse, CardCreate, CardBase

router = APIRouter(tags=["Cards"])


@router.post("/", response_model=CardResponse, response_model_exclude={"balance"})
def create_card(card: CardCreate,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    # Generates a random card number
    number = "".join([str(randint(0, 9)) for _ in range(16)])

    # Expiry date in a year
    expiration_date = datetime.now() + timedelta(days=365)

    # random CVV
    cvv = randint(100, 999)

    db_card = Card(user_id=user.id,
                   number=number,
                   expiration_date=expiration_date,
                   cvv=cvv,
                   type=card.type.value,
                   cardholder=card.cardholder,
                   design=card.design)

    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card
