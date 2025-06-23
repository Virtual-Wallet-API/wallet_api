import os
from enum import Enum
from typing import Dict

import requests
from requests import Response

from app.config import MAILGUN_API_KEY
from app.models import User


class NotificationType(str, Enum):
    UNIMPORTANT = "unimportant"
    IMPORTANT = "important"
    ALERT = "alert"
    URGENT = "urgent"


class EmailTemplates(dict, Enum):
    """Email templates"""
    ACCOUNT_ACTIVATED = {"subject": "Welcome to VWallet",
                         "body": """Welcome to VWallet, {user.username}!\n\n 
We're pleased to inform you that your VWallet account has been reviewed and activated. You can now log in at http://vwallet.ninja

If you have any questions, contact support at {support_email}.

Welcome to VWallet!
The VWallet Team"""}

    ACCOUNT_DEACTIVATED = {"subject": "Your account has been deactivated",
                           "body": """Dear {user.username},

Your VWallet account has been deactivated due to inactivity or policy violation. To reactivate, please log in twice within 7 days at http://vwallet.ninja

For assistance, contact us at admin@vwallet.ninja.

Best,
The VWallet Team"""}

    ACCOUNT_BLOCKED = {"subject": "Your account has been blocked",
                       "body": """Dear {user.username},

We regret to inform you that your VWallet account has been blocked following a staff decision. To appeal, contact admin@vwallet.ninja

Thank you,
The VWallet Team"""
                       }

    ACCOUNT_REACTIVATED = {"subject": "Your account has been reactivated",
                           "body": """Dear {user.username},

Great news! Your VWallet account has been reactivated. Log in at http://vwallet.ninja to resume using your wallet.

For questions, reach out to admin@vwallet.ninja

Welcome back!
The VWallet Team"""}

    INCOMING_TRANSACTION = {"subject": "New incoming transaction",
                            "body": """Dear {user.username},

You have an incoming transaction of {amount} {currency} awaiting your action. Review and accept or decline it at http://vwallet.ninja/receive

Best,
The VWallet Team"""
                            }

    OUTGOING_TRANSACTION = {"subject": "New outgoing transaction",
                            "body": """Dear {user.username},

An outgoing transaction of {amount} {currency} has been processed to {recipient}. View details at http://vwallet.ninja/send

If you did not initiate this, contact admin@vwallet.ninja immediately.

Best,
The VWallet Team"""}

    FAILED_RECURRING_TRANSACTION = {"subject": "Failed recurring transaction",
                                    "body": """Dear {user.username},

We couldn't process your recurring transaction of {amount} {currency}. Verify your payment details at http://vwallet.ninja/account

Contact admin@vwallet.ninja for assistance.

Thank you,
The VWallet Team"""
                                    }

    NEW_ADMIN_ACCOUNT = {"subject": "New admin account",
                         "body": """Dear {user.username},

Congratulations! Your VWallet account has been promoted to Administrator. 
For security, a randomly generated password has been generated for you. In order to proceed your must reset your password on your first login at http://vwallet.ninja/preset

Your one-time password is: {password}

Contact admin@vwallet.admin for support.

Best,
The VWallet Team"""
                         }

    EMAIL_VERIFICATION = {"subject": "Verify your email",
                          "body": """Dear {user.username},

Please follow this link to verify your email: {verification_link}{key}

Best,
The VWallet Team"""
                          }

    PASSWORD_RESET = {"subject": "Reset your VWallet password",
                     "body": """Dear {user.username},\n\nYou requested a password reset. Please follow this link to set a new password:\n{reset_link}\n\nIf you did not request this, please ignore this email.\n\nBest,\nThe VWallet Team"""}

    # Transaction Email Templates
    TRANSACTION_CREATED = {"subject": "Transaction Created - Confirmation Required",
                          "body": """Dear {user.username},

Your transaction has been created successfully! 

Transaction Details:
• Amount: ${amount:.2f}
• Recipient: {recipient_username}
• Description: {description}
• Transaction ID: {transaction_id}

⚠️ Action Required: Please log in to confirm this transaction and reserve the funds.
Until confirmed, this transaction is pending and no money has been transferred.

Confirm your transaction at: http://vwallet.ninja/send

Thank you,
The VWallet Team"""}

    TRANSACTION_RECEIVED = {"subject": "New Transaction Request Received",
                           "body": """Dear {user.username},

You have received a new transaction request!

Transaction Details:
• Amount: ${amount:.2f}
• From: {sender_username}
• Description: {description}
• Status: Waiting for sender confirmation

The sender needs to confirm this transaction before you can accept it.
You will receive another notification when it's ready for your action.

View your transactions at: http://vwallet.ninja/receive

Best regards,
The VWallet Team"""}

    TRANSACTION_CONFIRMED = {"subject": "Transaction Confirmed - Funds Reserved",
                            "body": """Dear {user.username},

Your transaction has been confirmed and funds have been reserved!

Transaction Details:
• Amount: ${amount:.2f}
• Recipient: {recipient_username}
• Description: {description}
• Transaction ID: {transaction_id}
• Status: Awaiting recipient acceptance

The funds are now reserved from your account and waiting for {recipient_username} to accept.
If they decline, the funds will be returned to your available balance.

Track your transaction at: http://vwallet.ninja/send

Best regards,
The VWallet Team"""}

    TRANSACTION_AWAITING_ACCEPTANCE = {"subject": "Transaction Ready - Action Required",
                                      "body": """Dear {user.username},

A transaction is ready for your acceptance!

Transaction Details:
• Amount: ${amount:.2f}
• From: {sender_username}
• Description: {description}
• Transaction ID: {transaction_id}

🎯 Action Required: The sender has confirmed and reserved the funds.
You can now accept or decline this transaction.

✅ Accept to receive the funds
❌ Decline to reject the transaction

Take action at: http://vwallet.ninja/receive

Best regards,
The VWallet Team"""}

    TRANSACTION_COMPLETED_SENDER = {"subject": "Transaction Completed Successfully",
                                   "body": """Dear {user.username},

Your transaction has been completed successfully! 🎉

Transaction Details:
• Amount: ${amount:.2f}
• Recipient: {recipient_username}
• Description: {description}
• Transaction ID: {transaction_id}
• Status: Completed

The funds have been transferred from your account to {recipient_username}.
Your account balance has been updated.

View transaction history at: http://vwallet.ninja/transactions

Thank you for using VWallet!
The VWallet Team"""}

    TRANSACTION_COMPLETED_RECEIVER = {"subject": "Payment Received Successfully",
                                     "body": """Dear {user.username},

You have received a payment! 💰

Transaction Details:
• Amount: ${amount:.2f}
• From: {sender_username}
• Description: {description}
• Transaction ID: {transaction_id}
• Status: Completed

The funds have been added to your account balance.

View your updated balance at: http://vwallet.ninja/account

Thank you for using VWallet!
The VWallet Team"""}

    TRANSACTION_DECLINED = {"subject": "Transaction Declined",
                           "body": """Dear {user.username},

Your transaction has been declined by the recipient.

Transaction Details:
• Amount: ${amount:.2f}
• Recipient: {recipient_username}
• Description: {description}
• Transaction ID: {transaction_id}
• Reason: {reason}

The reserved funds have been returned to your available balance.
No money was transferred.

View your account at: http://vwallet.ninja/account

Best regards,
The VWallet Team"""}

    TRANSACTION_CANCELLED = {"subject": "Transaction Cancelled",
                            "body": """Dear {user.username},

Your transaction has been cancelled.

Transaction Details:
• Amount: ${amount:.2f}
• Recipient: {recipient_username}
• Description: {description}
• Transaction ID: {transaction_id}

Any reserved funds have been returned to your available balance.
No money was transferred.

View your account at: http://vwallet.ninja/account

Best regards,
The VWallet Team"""}

    TRANSACTION_FAILED = {"subject": "Transaction Failed",
                         "body": """Dear {user.username},

Unfortunately, your transaction has failed.

Transaction Details:
• Amount: ${amount:.2f}
• Recipient: {recipient_username}
• Description: {description}
• Transaction ID: {transaction_id}
• Error: {error_message}

Any reserved funds have been returned to your available balance.
No money was transferred.

If this continues to happen, please contact support at admin@vwallet.ninja

Best regards,
The VWallet Team"""}

    def format(self, user, **kwargs):
        return {k: v.format(user=user,support_email='admin@vwallet.ninja', **kwargs) for k, v in self.value.items()}


class NotificationService:
    """Business logic for notification management"""

    @classmethod
    def email_factory(cls, to: User, subject: str = None, body: str = None) -> Dict:
        mail = {"from": "VWallet <admin@vwallet.ninja>",
                "to": f"{to.username} <{to.email}>",
                "subject": subject,
                "text": body}
        return mail

    @classmethod
    def send_email(cls, to: User, subject: str, body: str) -> Response:
        sent = requests.post(url="https://api.mailgun.net/v3/vwallet.ninja/messages",
                             auth=("api", os.getenv(MAILGUN_API_KEY, "Key_not_defined")),
                             data=cls.email_factory(to, subject, body))
        return sent

    @classmethod
    def notify_from_template(cls, template: EmailTemplates, user: User, **kwargs) -> Response:
        return cls.send_email(user, **template.format(user, **kwargs))

    @classmethod
    def notify(cls, user: User, title: str, message: str) -> Response:
        """Send a notification to a user"""
        return cls.send_email(user, title, message)
