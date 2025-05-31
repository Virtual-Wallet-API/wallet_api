import logging
import traceback

import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.business.payment import *
from app.business.stripe import *
from app.business.user import *
from app.models import Card
from app.models.currency import Currency
from app.models.deposit import Deposit
from app.models.user import User
from app.schemas.deposit import (
    DepositPaymentIntentCreate, DepositPaymentIntentResponse, DepositConfirm, DepositResponse, DepositWithCard
)

logger = logging.getLogger(__name__)


class StripeDepositService:
    """Business logic for deposit management with Stripe deposit integration"""

    @staticmethod
    async def create_deposit_payment_intent(db: Session,
                                            user: User,
                                            deposit_data: DepositPaymentIntentCreate) -> DepositPaymentIntentResponse:
        """
        Creates a deposit payment intent for a user using Stripe.

        This method ensures the user has appropriate permissions to make a deposit, validates and attaches the provided
        payment method to the user's Stripe customer, and creates a deposit record in the database. It generates a payment
        intent using the Stripe API and validates the payment method. The deposit and payment intent details are updated
        within the database.

        :param db: The database session used for querying and persisting objects.
        :param user: The user object associated with the deposit process.
        :param deposit_data: Contains the details of the deposit process, such as payment method, currency, and amount.
        :return: A response object containing the Stripe client secret, payment intent ID, amount, currency, status,
            and deposit ID.
        """
        # Verify user can deposit
        UAuth.verify_user_can_deposit(user)

        try:
            # Ensure user has Stripe customer
            stripe_customer_id = await StripeCardService.ensure_stripe_customer(db, user)
            stripe.PaymentMethod.attach(deposit_data.payment_method_id, customer=stripe_customer_id)

            # Get or create USD currency
            currency = db.query(Currency).filter(Currency.code == "USD").first()
            if not currency:
                currency = Currency(code="USD")
                db.add(currency)
                db.commit()
                db.refresh(currency)

            # Create deposit record first
            deposit = Deposit(user_id=user.id,
                              payment_method_last_four="0000",
                              currency_id=currency.id,
                              amount=deposit_data.amount_cents / 100,  # Convert cents to dollars
                              amount_cents=deposit_data.amount_cents,
                              deposit_type="card_payment",
                              method="stripe",
                              status="pending",
                              description=deposit_data.description)
            db.add(deposit)
            db.commit()

            # Create payment intent with Stripe
            payment_method = await StripeService.retrieve_payment_method(deposit_data.payment_method_id)
            try:
                payment_intent = await StripeService.create_payment_intent(
                    amount=deposit_data.amount_cents,
                    currency=deposit_data.currency,
                    customer_id=stripe_customer_id,
                    metadata={
                        "user_id": str(user.id),
                        "deposit_id": str(deposit.id),
                        "description": user.username + " Wallet deposit"
                    },
                    setup_future_usage="off_session" if deposit_data.save_payment_method else None,
                    payment_method=payment_method)

            except Exception as e:
                print("Error creating payment intent: " + str(e))
                raise HTTPException \
                    (status_code=400,
                     detail="Error creating payment intent with payment method ID " + \
                            str(deposit_data.payment_method_id))

            # Verify payment method is not in the database and if so that it belongs to this user
            card_last4 = payment_method["card"]["last4"]
            deposit.payment_method_last_four = card_last4

            # Card fingerprint check
            card_fingerprint = payment_method["card"]["fingerprint"]
            existing = CardService.validate_card_fingerprint(db, user, card_fingerprint)
            if type(existing) == type(Card):
                stripe.PaymentIntent.cancel(payment_intent["id"])
                deposit.status = "failed"
                db.commit()

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Card is already associated with another account"
                )

            # Update deposit with Stripe payment intent ID
            deposit.stripe_payment_intent_id = payment_intent["id"]
            deposit.stripe_customer_id = stripe_customer_id
            db.commit()
            db.refresh(deposit)

            logger.info(f"Created deposit payment intent {payment_intent['id']} for user {user.id}")

            return DepositPaymentIntentResponse(
                client_secret=payment_intent["client_secret"],
                payment_intent_id=payment_intent["client_secret"],
                amount=payment_intent["amount"],
                currency=payment_intent["currency"],
                status=payment_intent["status"],
                deposit_id=deposit.id
            )
        except CardError as e:
            str_error = f"{e}"
            error_reason = str_error.split(":")[1].strip()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_reason
            )
        except Exception as e:
            logger.error(f"Failed to create deposit payment intent for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{e}"
            )

    @staticmethod
    async def deposit_with_existing_card(db: Session,
                                         user: User,
                                         deposit_data: DepositWithCard) -> DepositPaymentIntentResponse:
        """
        This static method processes a deposit transaction using an existing card associated
        with the provided user. It involves validating the card, creating a deposit record,
        and interacting with Stripe to create, confirm, and finalize the payment intent.

        :param db: Database session for querying and persisting data
        :param user: The user performing the deposit operation
        :param deposit_data: Data related to the deposit request, including card details,
            currency, amount, and description
        :return: A response object containing the details of the payment intent created
            during the deposit process
        :raises HTTPException: If the card is not found, is inactive, or expired; if issues
            occur while processing the deposit with Stripe; or if any unexpected error happens
        """
        UAuth.verify_user_can_deposit(user)
        try:
            # Get the card
            card = db.query(Card).filter(
                Card.id == deposit_data.card_id,
                Card.user_id == user.id,
                Card.is_active == True
            ).first()

            if not card:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Card not found"
                )

            if card.is_expired:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot use expired card"
                )

            # Get currency
            currency = db.query(Currency).filter(Currency.code == deposit_data.currency_code).first()
            if not currency:
                currency = Currency(code=deposit_data.currency_code)
                db.add(currency)
                db.commit()
                db.refresh(currency)

            # Create deposit record
            deposit = Deposit(
                user_id=user.id,
                card_id=card.id,
                payment_method_last_four=card.last_four,
                currency_id=currency.id,
                amount=deposit_data.amount_cents / 100,
                amount_cents=deposit_data.amount_cents,
                deposit_type="card_payment",
                method="stripe",
                status="pending",
                description=deposit_data.description
            )

            db.add(deposit)
            db.commit()
            db.refresh(deposit)

            # Create payment intent with existing payment method
            payment_intent = await StripeService.create_payment_intent(
                amount=deposit_data.amount_cents,
                currency=deposit_data.currency_code.lower(),
                customer_id=user.stripe_customer_id,
                metadata={
                    "user_id": str(user.id),
                    "deposit_id": str(deposit.id),
                    "card_id": str(card.id),
                    "description": deposit_data.description or "Wallet deposit"
                }
            )

            # Confirm payment intent with saved payment method
            confirmed_payment = await StripeService.confirm_payment_intent(
                payment_intent["id"],
                card.stripe_payment_method_id
            )

            # Update deposit with Stripe info
            deposit.stripe_payment_intent_id = confirmed_payment["id"]
            deposit.stripe_customer_id = user.stripe_customer_id
            deposit.status = "processing"
            db.commit()
            db.refresh(deposit)

            logger.info(f"Created deposit with existing card {card.id} for user {user.id}")

            return DepositPaymentIntentResponse(
                client_secret=confirmed_payment["client_secret"],
                payment_intent_id=confirmed_payment["id"],
                amount=confirmed_payment["amount"],
                currency=confirmed_payment["currency"],
                status=confirmed_payment["status"],
                deposit_id=deposit.id
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create deposit with existing card for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process deposit"
            )

    @staticmethod
    async def confirm_deposit(db: Session,
                              user: User,
                              confirm_data: DepositConfirm) -> DepositResponse:
        """
        Confirms a deposit operation for a given user based on the provided confirmation data.
        This method retrieves the deposit based on payment intent ID, validates its status with
        Stripe, and accordingly updates the deposit status, user's balance, and potentially saves
        a payment card if requested. It handles various payment statuses such as succeeded,
        processing, or failed and ensures the database reflects the correct state.

        :param db: Database session to query and update deposit and user data.
        :param user: The user for whom the deposit is being confirmed.
        :param confirm_data: The data required to confirm the deposit, including payment intent ID
            and options to save the card.
        :return: The response model containing the updated deposit information.
        :raises HTTPException: If the deposit is not found, validation fails, or any server
            error occurs while processing the request.
        """
        try:
            # Get the deposit by payment intent ID
            payment_intent_id = confirm_data.payment_intent_id.split("_secret_")[0]
            deposit = db.query(Deposit).filter(
                Deposit.stripe_payment_intent_id == payment_intent_id,
                Deposit.user_id == user.id
            ).first()

            if not deposit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Deposit not found"
                )

            # Retrieve payment intent from Stripe to check status
            payment_intent = await StripeService.retrieve_payment_intent(payment_intent_id)
            if payment_intent["status"] == "succeeded":
                # Update deposit status
                deposit.mark_completed()

                # Update user balance
                user.balance += deposit.amount

                # Save card if requested and payment method exists
                pmethod = payment_intent.get("payment_method")
                if confirm_data.save_card and pmethod:
                    card = None
                    try:
                        card = await StripeCardService.save_card_from_payment_method(
                            db, user, pmethod,
                            user.username
                        )
                    except Exception as e:
                        traceback.print_tb(e.__traceback__)
                        logger.warning(f"Failed to save card for user {user.id}: {e}")

                    deposit.card_id = card.id if card else None

                # Update Stripe charge ID if available
                if payment_intent.get("charges", {}).get("data"):
                    charge = payment_intent["charges"]["data"][0]
                    deposit.stripe_charge_id = charge["id"]

                db.commit()
                db.refresh(deposit)
                db.refresh(user)

                logger.info(f"Confirmed deposit {deposit.id} for user {user.id}, new balance: ${user.balance}")

            elif payment_intent["status"] == "requires_action":
                deposit.status = "processing"
                db.commit()
                db.refresh(deposit)

            elif payment_intent["status"] in ["canceled", "payment_failed"]:
                deposit.mark_failed("Payment failed or was canceled")
                db.commit()
                db.refresh(deposit)

            return DepositResponse.model_validate(deposit)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to confirm deposit for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to confirm deposit"
            )
