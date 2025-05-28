from datetime import datetime
from enum import Enum
from typing import Dict

import httpx

from app.config import MAILJET_API_KEY, MAILJET_SECRET, MAILJET_FROM_EMAIL
from app.models import User


def send_email_test():
    payload = {
        "Messages": [
            {
                "From": {
                    "Email": MAILJET_FROM_EMAIL,
                    "Name": "Siso"
                },
                "To": [
                    {"Email": "martin.kitukov@gmail.com", "Name": "Marto"},
                    {"Email": "steliyan.slavov31@gmail.com","Name": "Steliyan"}
                ],
                "Subject": "Testing Mailjet",
                "TextPart": """
                                Hello, this is a test email. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus sit amet aliquet sem.
                                Vivamus sit amet aliquet sem. Vivamus sit amet aliquet sem. Vivamus sit amet aliquet sem. Vivamus sit amet aliquet sem.
                            """,
                "HTMLPart": f"<h3><p style='color:red;'>Testing red color html</p></h3><br />May the delivery force be with you!"
            }
        ]
    }

    try:
        with httpx.Client() as client:
            response = client.post(
                "https://api.mailjet.com/v3.1/send",
                auth=(MAILJET_API_KEY, MAILJET_SECRET),
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            print(response.json())
            response.raise_for_status()
        return True, "Successfully sent email"
    except httpx.HTTPStatusError as e:
        return False, f"Failed to send email: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return False, f"Failed to send email: {str(e)}"


def get_sent_emails():
    try:
        with httpx.Client() as client:
            params = {"Limit": 5}
            response = client.get(
                "https://api.mailjet.com/v3/REST/message",
                auth=(MAILJET_API_KEY, MAILJET_SECRET),
                params=params
            )
            response.raise_for_status()
            data = response.json()
            print(data)
            messages = []
            for msg in data.get("Data", []):
                to_field = msg.get("To", [])
                recipient = to_field[0].get("Email", "") if to_field else "Unknown"
                messages.append({
                    "message_id": msg.get("ID"),
                    "recipient": recipient,
                    "subject": msg.get("Subject", ""),
                    "status": msg.get("Status", "unknown"),
                    "sent_at": msg.get("CreatedAt", datetime.utcnow().isoformat())
                })
            print(messages)
            return messages
    except httpx.HTTPStatusError as e:
        return [{"error": f"Failed to fetch sent messages: {e.response.status_code} - {e.response.text}"}]
    except httpx.RequestError as e:
        return [{"error": f"Failed to fetch sent messages: {str(e)}"}]


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
        send_email_test()
        pass

    @classmethod
    def mark_notification_as_read(cls, user: User, notification_id: int) -> bool:
        """Mark a notification as read"""
        # raise HTTPException(status_code=501, detail="Not implemented yet")
        pass
