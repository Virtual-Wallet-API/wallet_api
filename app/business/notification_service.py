from enum import Enum
from typing import Dict
from app.models import User
import httpx


class NotificationType(str, Enum):
    UNIMPORTANT = "unimportant"
    IMPORTANT = "important"
    ALERT = "alert"
    URGENT = "urgent"


class NotificationService:
    """Business logic for notification management"""

    @classmethod
    def notify(cls, user: User, message: Dict[str, str]) -> bool:
        """Send a notification to a user"""
        # message = {
        #     "title": "Notification title",
        #     "body": "Notification body",
        #     "type": NotificationType
        # }
        # raise HTTPException(status_code=501, detail="Not implemented yet")
        pass

    @classmethod
    def mark_notification_as_read(cls, user: User, notification_id: int) -> bool:
        """Mark a notification as read"""
        # raise HTTPException(status_code=501, detail="Not implemented yet")
        pass
