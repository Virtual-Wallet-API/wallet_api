"""
Unit tests for StripeService business logic.
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
import stripe

from tests.base_test import BaseTestCase
from app.business.stripe.stripe_service import StripeService


class TestStripeService(BaseTestCase):
    """Test cases for StripeService."""

    def setUp(self):
        super().setUp()
        # Mock Stripe objects
        self.mock_customer = {
            "id": "cus_test123",
            "email": "test@example.com",
            "name": "Test User",
            "metadata": {}
        }

        self.mock_payment_intent = {
            "id": "pi_test123",
            "amount": 10000,
            "currency": "usd",
            "status": "requires_payment_method",
            "client_secret": "pi_test123_secret_test",
            "metadata": {}
        }

        self.mock_setup_intent = {
            "id": "seti_test123",
            "client_secret": "seti_test123_secret_test",
            "status": "requires_payment_method",
            "usage": "off_session",
            "metadata": {}
        }

        self.mock_payment_method = {
            "id": "pm_test123",
            "type": "card",
            "card": {
                "brand": "visa",
                "last4": "1234",
                "fingerprint": "fp_test123"
            },
            "customer": "cus_test123"
        }

        self.mock_refund = {
            "id": "re_test123",
            "amount": 5000,
            "payment_intent": "pi_test123",
            "status": "succeeded",
            "metadata": {}
        }

        self.mock_payout = {
            "id": "po_test123",
            "amount": 10000,
            "currency": "usd",
            "method": "instant",
            "status": "paid",
            "metadata": {}
        }

    @patch('app.business.stripe.stripe_service.stripe.Customer.create')
    def test_create_customer_success(self, mock_create):
        """Test successful customer creation."""
        # Arrange
        mock_create.return_value = self.mock_customer

        # Act
        async def run_test():
            return await StripeService.create_customer(
                email="test@example.com",
                name="Test User"
            )

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, self.mock_customer)
        mock_create.assert_called_once_with(
            email="test@example.com",
            name="Test User",
            metadata={}
        )

    @patch('app.business.stripe.stripe_service.stripe.Customer.create')
    def test_create_customer_with_metadata(self, mock_create):
        """Test customer creation with metadata."""
        # Arrange
        metadata = {"user_id": "123", "source": "app"}
        customer_with_metadata = {**self.mock_customer, "metadata": metadata}
        mock_create.return_value = customer_with_metadata

        # Act
        async def run_test():
            return await StripeService.create_customer(
                email="test@example.com",
                name="Test User",
                metadata=metadata
            )

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, customer_with_metadata)
        mock_create.assert_called_once_with(
            email="test@example.com",
            name="Test User",
            metadata=metadata
        )

    @patch('app.business.stripe.stripe_service.stripe.Customer.create')
    def test_create_customer_stripe_error(self, mock_create):
        """Test customer creation with Stripe error."""
        # Arrange
        mock_create.side_effect = stripe.error.StripeError("Invalid email")

        # Act & Assert
        async def run_test():
            await StripeService.create_customer(
                email="invalid-email",
                name="Test User"
            )

        with self.assertRaises(stripe.error.StripeError):
            asyncio.run(run_test())

    @patch('app.business.stripe.stripe_service.stripe.PaymentIntent.create')
    def test_create_payment_intent_success(self, mock_create):
        """Test successful payment intent creation."""
        # Arrange
        mock_create.return_value = self.mock_payment_intent
        payment_method = {"type": "card", "card": {"number": "4242424242424242"}}

        # Act
        async def run_test():
            return await StripeService.create_payment_intent(
                amount=10000,
                currency="usd",
                payment_method=payment_method,
                customer_id="cus_test123"
            )

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, self.mock_payment_intent)
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args["amount"], 10000)
        self.assertEqual(call_args["currency"], "usd")
        self.assertEqual(call_args["customer"], "cus_test123")
        self.assertEqual(call_args["payment_method"], payment_method)

    def test_create_payment_intent_no_payment_method(self):
        """Test payment intent creation fails without payment method."""
        # Act & Assert
        async def run_test():
            await StripeService.create_payment_intent(amount=10000)

        with self.assertRaises(HTTPException) as context:
            asyncio.run(run_test())

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Payment method is required", context.exception.detail)

    @patch('app.business.stripe.stripe_service.stripe.PaymentIntent.create')
    def test_create_payment_intent_with_setup_future_usage(self, mock_create):
        """Test payment intent creation with setup_future_usage."""
        # Arrange
        mock_create.return_value = self.mock_payment_intent
        payment_method = {"type": "card"}

        # Act
        async def run_test():
            return await StripeService.create_payment_intent(
                amount=10000,
                payment_method=payment_method,
                setup_future_usage="off_session"
            )

        result = asyncio.run(run_test())

        # Assert
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args["setup_future_usage"], "off_session")

    @patch('app.business.stripe.stripe_service.stripe.PaymentIntent.create')
    def test_create_payment_intent_stripe_error(self, mock_create):
        """Test payment intent creation with Stripe error."""
        # Arrange
        mock_create.side_effect = stripe.error.CardError("Card declined", None, "card_declined")
        payment_method = {"type": "card"}

        # Act & Assert
        async def run_test():
            await StripeService.create_payment_intent(
                amount=10000,
                payment_method=payment_method
            )

        with self.assertRaises(stripe.error.CardError):
            asyncio.run(run_test())

    @patch('app.business.stripe.stripe_service.stripe.PaymentIntent.retrieve')
    def test_retrieve_payment_intent_success(self, mock_retrieve):
        """Test successful payment intent retrieval."""
        # Arrange
        mock_retrieve.return_value = self.mock_payment_intent

        # Act
        async def run_test():
            return await StripeService.retrieve_payment_intent("pi_test123")

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, self.mock_payment_intent)
        mock_retrieve.assert_called_once_with("pi_test123")

    @patch('app.business.stripe.stripe_service.stripe.PaymentIntent.retrieve')
    def test_retrieve_payment_intent_stripe_error(self, mock_retrieve):
        """Test payment intent retrieval with Stripe error."""
        # Arrange
        mock_retrieve.side_effect = stripe.error.InvalidRequestError("No such payment_intent", None)

        # Act & Assert
        async def run_test():
            await StripeService.retrieve_payment_intent("pi_invalid")

        with self.assertRaises(stripe.error.InvalidRequestError):
            asyncio.run(run_test())

    @patch('app.business.stripe.stripe_service.stripe.PaymentIntent.confirm')
    def test_confirm_payment_intent_success(self, mock_confirm):
        """Test successful payment intent confirmation."""
        # Arrange
        confirmed_payment_intent = {**self.mock_payment_intent, "status": "succeeded"}
        mock_confirm.return_value = confirmed_payment_intent

        # Act
        async def run_test():
            return await StripeService.confirm_payment_intent("pi_test123", "pm_test123")

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, confirmed_payment_intent)
        mock_confirm.assert_called_once_with("pi_test123", payment_method="pm_test123")

    @patch('app.business.stripe.stripe_service.stripe.PaymentIntent.confirm')
    def test_confirm_payment_intent_stripe_error(self, mock_confirm):
        """Test payment intent confirmation with Stripe error."""
        # Arrange
        mock_confirm.side_effect = stripe.error.CardError("Authentication required", None, "authentication_required")

        # Act & Assert
        async def run_test():
            await StripeService.confirm_payment_intent("pi_test123", "pm_test123")

        with self.assertRaises(stripe.error.CardError):
            asyncio.run(run_test())

    @patch('app.business.stripe.stripe_service.stripe.SetupIntent.create')
    def test_create_setup_intent_success(self, mock_create):
        """Test successful setup intent creation."""
        # Arrange
        mock_create.return_value = self.mock_setup_intent

        # Act
        async def run_test():
            return await StripeService.create_setup_intent("cus_test123")

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, self.mock_setup_intent)
        mock_create.assert_called_once_with(
            customer="cus_test123",
            usage="off_session",
            automatic_payment_methods={"enabled": True},
            metadata={}
        )

    @patch('app.business.stripe.stripe_service.stripe.SetupIntent.create')
    def test_create_setup_intent_with_metadata(self, mock_create):
        """Test setup intent creation with custom metadata."""
        # Arrange
        metadata = {"purpose": "save_card"}
        setup_intent_with_metadata = {**self.mock_setup_intent, "metadata": metadata}
        mock_create.return_value = setup_intent_with_metadata

        # Act
        async def run_test():
            return await StripeService.create_setup_intent(
                customer_id="cus_test123",
                usage="on_session",
                metadata=metadata
            )

        result = asyncio.run(run_test())

        # Assert
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args["usage"], "on_session")
        self.assertEqual(call_args["metadata"], metadata)

    @patch('app.business.stripe.stripe_service.stripe.SetupIntent.create')
    def test_create_setup_intent_stripe_error(self, mock_create):
        """Test setup intent creation with Stripe error."""
        # Arrange
        mock_create.side_effect = stripe.error.InvalidRequestError("No such customer", None)

        # Act & Assert
        async def run_test():
            await StripeService.create_setup_intent("cus_invalid")

        with self.assertRaises(stripe.error.InvalidRequestError):
            asyncio.run(run_test())

    @patch('app.business.stripe.stripe_service.stripe.PaymentMethod.list')
    def test_list_payment_methods_success(self, mock_list):
        """Test successful payment methods listing."""
        # Arrange
        payment_methods_response = {
            "object": "list",
            "data": [self.mock_payment_method],
            "has_more": False
        }
        mock_list.return_value = payment_methods_response

        # Act
        async def run_test():
            return await StripeService.list_payment_methods("cus_test123")

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, payment_methods_response)
        mock_list.assert_called_once_with(customer="cus_test123", type="card")

    @patch('app.business.stripe.stripe_service.stripe.PaymentMethod.list')
    def test_list_payment_methods_different_type(self, mock_list):
        """Test payment methods listing with different type."""
        # Arrange
        mock_list.return_value = {"object": "list", "data": []}

        # Act
        async def run_test():
            return await StripeService.list_payment_methods("cus_test123", type="us_bank_account")

        result = asyncio.run(run_test())

        # Assert
        mock_list.assert_called_once_with(customer="cus_test123", type="us_bank_account")

    @patch('app.business.stripe.stripe_service.stripe.PaymentMethod.list')
    def test_list_payment_methods_stripe_error(self, mock_list):
        """Test payment methods listing with Stripe error."""
        # Arrange
        mock_list.side_effect = stripe.error.InvalidRequestError("No such customer", None)

        # Act & Assert
        async def run_test():
            await StripeService.list_payment_methods("cus_invalid")

        with self.assertRaises(stripe.error.InvalidRequestError):
            asyncio.run(run_test())

    @patch('app.business.stripe.stripe_service.stripe.PaymentMethod.retrieve')
    def test_retrieve_payment_method_success(self, mock_retrieve):
        """Test successful payment method retrieval."""
        # Arrange
        mock_retrieve.return_value = self.mock_payment_method

        # Act
        async def run_test():
            return await StripeService.retrieve_payment_method("pm_test123")

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, self.mock_payment_method)
        mock_retrieve.assert_called_once_with("pm_test123")

    @patch('app.business.stripe.stripe_service.stripe.PaymentMethod.retrieve')
    def test_retrieve_payment_method_stripe_error(self, mock_retrieve):
        """Test payment method retrieval with Stripe error."""
        # Arrange
        mock_retrieve.side_effect = stripe.error.InvalidRequestError("No such payment_method", None)

        # Act & Assert
        async def run_test():
            await StripeService.retrieve_payment_method("pm_invalid")

        with self.assertRaises(stripe.error.InvalidRequestError):
            asyncio.run(run_test())

    @patch('app.business.stripe.stripe_service.StripeService.retrieve_payment_method')
    def test_retrieve_payment_method_fingerprint_success(self, mock_retrieve):
        """Test successful payment method fingerprint retrieval."""
        # Arrange
        mock_retrieve.return_value = self.mock_payment_method

        # Act
        async def run_test():
            return await StripeService.retrieve_payment_method_fingerprting("pm_test123")

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, "fp_test123")
        mock_retrieve.assert_called_once_with("pm_test123")

    @patch('app.business.stripe.stripe_service.stripe.PaymentMethod.detach')
    def test_detach_payment_method_success(self, mock_detach):
        """Test successful payment method detachment."""
        # Arrange
        detached_payment_method = {**self.mock_payment_method, "customer": None}
        mock_detach.return_value = detached_payment_method

        # Act
        async def run_test():
            return await StripeService.detach_payment_method("pm_test123")

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, detached_payment_method)
        mock_detach.assert_called_once_with("pm_test123")

    @patch('app.business.stripe.stripe_service.stripe.PaymentMethod.detach')
    def test_detach_payment_method_stripe_error(self, mock_detach):
        """Test payment method detachment with Stripe error."""
        # Arrange
        mock_detach.side_effect = stripe.error.InvalidRequestError("No such payment_method", None)

        # Act & Assert
        async def run_test():
            await StripeService.detach_payment_method("pm_invalid")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(run_test())

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Error detaching payment method", context.exception.detail)

    @patch('app.business.stripe.stripe_service.stripe.PaymentMethod.detach')
    def test_detach_payment_method_general_error(self, mock_detach):
        """Test payment method detachment with general error."""
        # Arrange
        mock_detach.side_effect = Exception("Network error")

        # Act & Assert
        async def run_test():
            await StripeService.detach_payment_method("pm_test123")

        with self.assertRaises(HTTPException) as context:
            asyncio.run(run_test())

        self.assertEqual(context.exception.status_code, 400)

    @patch('app.business.stripe.stripe_service.stripe.Refund.create')
    def test_create_refund_success(self, mock_create):
        """Test successful refund creation."""
        # Arrange
        mock_create.return_value = self.mock_refund

        # Act
        async def run_test():
            return await StripeService.create_refund("pi_test123")

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, self.mock_refund)
        mock_create.assert_called_once_with(
            payment_intent="pi_test123",
            metadata={}
        )

    @patch('app.business.stripe.stripe_service.stripe.Refund.create')
    def test_create_refund_with_amount_and_reason(self, mock_create):
        """Test refund creation with amount and reason."""
        # Arrange
        refund_with_details = {**self.mock_refund, "amount": 3000, "reason": "requested_by_customer"}
        mock_create.return_value = refund_with_details

        # Act
        async def run_test():
            return await StripeService.create_refund(
                payment_intent_id="pi_test123",
                amount=3000,
                reason="requested_by_customer",
                metadata={"refund_reason": "customer_request"}
            )

        result = asyncio.run(run_test())

        # Assert
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args["amount"], 3000)
        self.assertEqual(call_args["reason"], "requested_by_customer")
        self.assertEqual(call_args["metadata"], {"refund_reason": "customer_request"})

    @patch('app.business.stripe.stripe_service.stripe.Refund.create')
    def test_create_refund_stripe_error(self, mock_create):
        """Test refund creation with Stripe error."""
        # Arrange
        mock_create.side_effect = stripe.error.InvalidRequestError("Charge already refunded", None)

        # Act & Assert
        async def run_test():
            await StripeService.create_refund("pi_test123")

        with self.assertRaises(stripe.error.InvalidRequestError):
            asyncio.run(run_test())

    @patch('app.business.stripe.stripe_service.stripe.Payout.create')
    def test_create_payout_success(self, mock_create):
        """Test successful payout creation."""
        # Arrange
        mock_create.return_value = self.mock_payout

        # Act
        async def run_test():
            return await StripeService.create_payout(
                amount=10000,
                currency="usd",
                method="instant"
            )

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, self.mock_payout)
        mock_create.assert_called_once_with(
            amount=10000,
            currency="usd",
            method="instant",
            metadata={}
        )

    @patch('app.business.stripe.stripe_service.stripe.Payout.create')
    def test_create_payout_with_destination(self, mock_create):
        """Test payout creation with destination."""
        # Arrange
        payout_with_destination = {**self.mock_payout, "destination": "card_test123"}
        mock_create.return_value = payout_with_destination

        # Act
        async def run_test():
            return await StripeService.create_payout(
                amount=5000,
                destination="card_test123",
                metadata={"user_id": "123"}
            )

        result = asyncio.run(run_test())

        # Assert
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args["destination"], "card_test123")
        self.assertEqual(call_args["metadata"], {"user_id": "123"})

    @patch('app.business.stripe.stripe_service.stripe.Payout.create')
    def test_create_payout_stripe_error(self, mock_create):
        """Test payout creation with Stripe error."""
        # Arrange
        mock_create.side_effect = stripe.error.InvalidRequestError("Insufficient funds", None)

        # Act & Assert
        async def run_test():
            await StripeService.create_payout(amount=10000)

        with self.assertRaises(stripe.error.InvalidRequestError):
            asyncio.run(run_test())

    @patch('app.business.stripe.stripe_service.stripe.Transfer.create_reversal')
    def test_create_reverse_transfer_success(self, mock_create_reversal):
        """Test successful reverse transfer creation."""
        # Arrange
        mock_reverse_transfer = {
            "id": "trr_test123",
            "amount": 5000,
            "transfer": "tr_test123",
            "metadata": {}
        }
        mock_create_reversal.return_value = mock_reverse_transfer

        # Act
        async def run_test():
            return await StripeService.create_reverse_transfer("tr_test123")

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, mock_reverse_transfer)
        mock_create_reversal.assert_called_once_with("tr_test123", metadata={})

    @patch('app.business.stripe.stripe_service.stripe.Transfer.create_reversal')
    def test_create_reverse_transfer_with_amount(self, mock_create_reversal):
        """Test reverse transfer creation with specific amount."""
        # Arrange
        mock_reverse_transfer = {"id": "trr_test123", "amount": 3000}
        mock_create_reversal.return_value = mock_reverse_transfer

        # Act
        async def run_test():
            return await StripeService.create_reverse_transfer(
                transfer_id="tr_test123",
                amount=3000,
                metadata={"reason": "dispute"}
            )

        result = asyncio.run(run_test())

        # Assert
        call_args = mock_create_reversal.call_args
        self.assertEqual(call_args[0][0], "tr_test123")  # transfer_id
        self.assertEqual(call_args[1]["amount"], 3000)
        self.assertEqual(call_args[1]["metadata"], {"reason": "dispute"})

    @patch('app.business.stripe.stripe_service.stripe.Transfer.create_reversal')
    def test_create_reverse_transfer_stripe_error(self, mock_create_reversal):
        """Test reverse transfer creation with Stripe error."""
        # Arrange
        mock_create_reversal.side_effect = stripe.error.InvalidRequestError("No such transfer", None)

        # Act & Assert
        async def run_test():
            await StripeService.create_reverse_transfer("tr_invalid")

        with self.assertRaises(stripe.error.InvalidRequestError):
            asyncio.run(run_test())

    @patch('app.business.stripe.stripe_service.stripe.Refund.create')
    def test_refund_to_source_success(self, mock_create):
        """Test successful refund to source creation."""
        # Arrange
        refund_to_source = {**self.mock_refund, "charge": "ch_test123"}
        mock_create.return_value = refund_to_source

        # Act
        async def run_test():
            return await StripeService.refund_to_source("ch_test123")

        result = asyncio.run(run_test())

        # Assert
        self.assertEqual(result, refund_to_source)
        mock_create.assert_called_once_with(
            charge="ch_test123",
            metadata={}
        )

    @patch('app.business.stripe.stripe_service.stripe.Refund.create')
    def test_refund_to_source_with_details(self, mock_create):
        """Test refund to source with amount and reason."""
        # Arrange
        refund_with_details = {
            **self.mock_refund,
            "charge": "ch_test123",
            "amount": 2500,
            "reason": "fraudulent"
        }
        mock_create.return_value = refund_with_details

        # Act
        async def run_test():
            return await StripeService.refund_to_source(
                charge_id="ch_test123",
                amount=2500,
                reason="fraudulent",
                metadata={"dispute_id": "dp_123"}
            )

        result = asyncio.run(run_test())

        # Assert
        call_args = mock_create.call_args[1]
        self.assertEqual(call_args["charge"], "ch_test123")
        self.assertEqual(call_args["amount"], 2500)
        self.assertEqual(call_args["reason"], "fraudulent")
        self.assertEqual(call_args["metadata"], {"dispute_id": "dp_123"})

    @patch('app.business.stripe.stripe_service.stripe.Refund.create')
    def test_refund_to_source_stripe_error(self, mock_create):
        """Test refund to source with Stripe error."""
        # Arrange
        mock_create.side_effect = stripe.error.InvalidRequestError("No such charge", None)

        # Act & Assert
        async def run_test():
            await StripeService.refund_to_source("ch_invalid")

        with self.assertRaises(stripe.error.InvalidRequestError):
            asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()