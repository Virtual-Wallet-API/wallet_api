from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import  Card
from app.schemas.card import CardPrivateResponse, CardCreate

router = APIRouter(tags=["Cards"])


@router.post("/", response_model=CardPrivateResponse, response_model_exclude={"user"})
def create_card(card:CardCreate, db: Session = Depends(get_db)):
    db_card = Card(**card.model_dump())
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card