import os
from enum import Enum
from typing import Dict

import requests
from requests import Response

from app.config import MAILGUN_API_KEY
from app.models import User


def send_mail() -> Response:
    return requests.post(
        url="https://api.mailgun.net/v3/vwallet.ninja/messages",
        auth=("api", os.getenv(MAILGUN_API_KEY, MAILGUN_API_KEY)),
        data={
            "from": "VWallet Notification <admin@vwallet.ninja>",
            "to": "Steliyan Svetoslavov Slavov <steliyan.slavov31@icloud.com>",
            "subject": "Hello Steliyan Svetoslavov Slavov",
            "text": "Congratulations Steliyan Svetoslavov Slavov, you just sent an email with Mailgun! You are truly awesome!"
        })


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
        response = send_mail()
        print(response.json())
        pass

    @classmethod
    def mark_notification_as_read(cls, user: User, notification_id: int) -> bool:
        """Mark a notification as read"""
        # raise HTTPException(status_code=501, detail="Not implemented yet")
        pass
