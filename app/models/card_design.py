from enum import Enum

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as CEnum

from app.infrestructure import Base
from app.models import Card


class DesignPatterns(str, Enum):
    GRID = "grid"
    STRIPES = "stripes"
    DOTS = "dots"


class CardDesign(Base):
    __tablename__ = 'card_designs'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id", name="card_designs_card_id_fk"), nullable=False, unique=True)

    pattern = Column(CEnum(DesignPatterns, name="design_patterns", values_callable=lambda obj: [e.value for e in obj]), nullable=False)

    color = Column(String, nullable=False)
    params = Column(String, nullable=False)

    card = relationship("Card", back_populates="design", foreign_keys=[card_id], uselist=False, single_parent=True)