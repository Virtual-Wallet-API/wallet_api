import stripe
from typing import Dict, Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import STRIPE_SECRET_KEY
import logging

from app.models import User, Card

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class StripeService:
    """Service for handling Stripe API interactions"""

    @staticmethod
    async def create_customer(email: str, name: str, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {e}")
            raise e

    @staticmethod
    async def create_payment_intent(
            amount: int,
            currency: str = "usd",
            customer_id: Optional[str] = None,
            metadata: Optional[Dict[str, str]] = None,
            setup_future_usage: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a payment intent for card payments"""
        try:
            payment_intent_data = {
                "amount": amount,  # Amount in cents
                "currency": currency,
                "automatic_payment_methods": {"enabled": True},
                "metadata": metadata or {}
            }

            if customer_id:
                payment_intent_data["customer"] = customer_id

            if setup_future_usage:
                payment_intent_data["setup_future_usage"] = setup_future_usage

            payment_intent = stripe.PaymentIntent.create(**payment_intent_data)
            return payment_intent
        except stripe.error.StripeError as e:
            logger.error(f"Error creating payment intent: {e}")
            raise e

    @staticmethod
    async def retrieve_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """Retrieve a payment intent"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return payment_intent
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment intent: {e}")
            raise e

    @staticmethod
    async def confirm_payment_intent(payment_intent_id: str, payment_method_id: str) -> Dict[str, Any]:
        """Confirm a payment intent with a payment method"""
        try:
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method=payment_method_id
            )
            return payment_intent
        except stripe.error.StripeError as e:
            logger.error(f"Error confirming payment intent: {e}")
            raise e

    @staticmethod
    async def create_setup_intent(
            customer_id: str,
            usage: str = "off_session",
            metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a setup intent for saving payment methods"""
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                usage=usage,
                automatic_payment_methods={"enabled": True},
                metadata=metadata or {}
            )
            return setup_intent
        except stripe.error.StripeError as e:
            logger.error(f"Error creating setup intent: {e}")
            raise e

    @staticmethod
    async def list_payment_methods(customer_id: str, type: str = "card") -> Dict[str, Any]:
        """List payment methods for a customer"""
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type=type
            )
            return payment_methods
        except stripe.error.StripeError as e:
            logger.error(f"Error listing payment methods: {e}")
            raise e

    @staticmethod
    async def retrieve_payment_method(payment_method_id: str) -> Dict[str, Any]:
        """Retrieve a specific payment method"""
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            return payment_method
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment method: {e}")
            raise e

    @staticmethod
    async def retrieve_payment_method_fingerprting(payment_method_id: str) -> str:
        """Retrieve a payment method (card) fingerprint"""
        payment_method = await StripeService.retrieve_payment_method(payment_method_id)
        return payment_method["card"]["fingerprint"]

    @staticmethod
    async def verify_payment_method_saved(payment_method_id: str, user: User, db: Session) -> str:
        """Retrieve a payment method (card) fingerprint"""
        payment_method = await StripeService.retrieve_payment_method(payment_method_id)
        fingerprint = payment_method["card"]["fingerprint"]
        card = db.query(Card).filter(Card.stripe_card_fingerprint == fingerprint).first()

        if card:
            if card.user_id != user.id:
                raise HTTPException(status_code=400, detail="This card is associated with another account")

    @staticmethod
    async def detach_payment_method(payment_method_id: str) -> Dict[str, Any]:
        """Detach a payment method from a customer"""
        try:
            payment_method = stripe.PaymentMethod.detach(payment_method_id)
            return payment_method
        except stripe.error.StripeError as e:
            logger.error(f"Error detaching payment method: {e}")
            raise e

    @staticmethod
    async def create_refund(
            payment_intent_id: str,
            amount: Optional[int] = None,
            reason: Optional[str] = None,
            metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a refund for a payment"""
        try:
            refund_data = {
                "payment_intent": payment_intent_id,
                "metadata": metadata or {}
            }

            if amount:
                refund_data["amount"] = amount

            if reason:
                refund_data["reason"] = reason

            refund = stripe.Refund.create(**refund_data)
            return refund
        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund: {e}")
            raise e

    # Withdrawal methods
    @staticmethod
    async def create_payout(
            amount: int,
            currency: str = "usd",
            method: str = "instant",
            destination: str = None,
            metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a payout to a debit card (requires Stripe Connect)"""
        try:
            payout_data = {
                "amount": amount,
                "currency": currency,
                "method": method,
                "metadata": metadata or {}
            }

            if destination:
                payout_data["destination"] = destination

            payout = stripe.Payout.create(**payout_data)
            return payout
        except stripe.error.StripeError as e:
            logger.error(f"Error creating payout: {e}")
            raise e

    @staticmethod
    async def create_reverse_transfer(
            transfer_id: str,
            amount: Optional[int] = None,
            metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a reverse transfer (for Stripe Connect)"""
        try:
            reverse_data = {
                "metadata": metadata or {}
            }

            if amount:
                reverse_data["amount"] = amount

            reverse = stripe.Transfer.create_reversal(
                transfer_id,
                **reverse_data
            )
            return reverse
        except stripe.error.StripeError as e:
            logger.error(f"Error creating reverse transfer: {e}")
            raise e

    @staticmethod
    async def refund_to_source(
            charge_id: str,
            amount: Optional[int] = None,
            reason: Optional[str] = None,
            metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Refund a charge back to the original payment source"""
        try:
            refund_data = {
                "charge": charge_id,
                "metadata": metadata or {}
            }

            if amount:
                refund_data["amount"] = amount

            if reason:
                refund_data["reason"] = reason

            refund = stripe.Refund.create(**refund_data)
            return refund
        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund to source: {e}")
            raise e 