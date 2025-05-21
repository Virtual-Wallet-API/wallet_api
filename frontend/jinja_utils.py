from enum import Enum

from jinja2 import Environment, FileSystemLoader

jenv = Environment(loader=FileSystemLoader("frontend/templates"))


class CardStatuses(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    LOST = "lost"
    UNKNOWN = "unknown"

## Card statuses
def card_status(card: dict):
    if not card or not card.get("status"):
        return CardStatuses.UNKNOWN.value
    try:
        return CardStatuses(card.get("status").lower()).value
    except ValueError:
        return CardStatuses.UNKNOWN.value

jenv.filters["card_status"] = card_status