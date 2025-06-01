"""
Unit tests for WithdrawalService business logic.
"""
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi import HTTPException

from tests.base_test import BaseTestCase
from app.business.payment.payment_withdrawal import WithdrawalService
from app.models import User, Withdrawal, Currency, Card, WStatus, WType, WMethod
from app.schemas.withdrawal import (
    WithdrawalCreate, WithdrawalUpdate, WithdrawalResponse,
    WithdrawalPublicResponse, WithdrawalHistoryResponse, WithdrawalStatsResponse
)


class TestWithdrawalService(BaseTestCase):
    """Test cases for WithdrawalService."""

    def setUp(self):
        super().setUp()
        self.user = self._create_mock_user(user_id=1, balance=1000.0)

        # Create properly typed mock withdrawal using enhanced base method
        self.mock_withdrawal = self._create_mock_withdrawal(
            withdrawal_id=1,
            user_id=self.user.id,
            status=WStatus.PENDING
        )

        # Setup user withdrawal collections for methods that iterate over them
        self.user.withdrawals = [self.mock_withdrawal]
        self.user.completed_withdrawals = []
        self.user.pending_withdrawals = [self.mock_withdrawal]
        self.user.failed_withdrawals = []
        self.user.refunds = []
        self.user.payouts = [self.mock_withdrawal]
        self.user.total_withdrawal_amount = 100.0
        self.user.total_pending_withdrawal_amount = 100.0

        # Setup currency mock
        self.mock_currency = Mock()
        self.mock_currency.id = 1
        self.mock_currency.name = "USD"
        self.mock_currency.symbol = "$"

        # Setup database query mock
        self.mock_query = Mock()
        self.mock_query.filter.return_value.first.return_value = self.mock_withdrawal
        self.mock_query.filter.return_value.all.return_value = [self.mock_withdrawal]
        self.mock_query.limit.return_value.all.return_value = [self.mock_withdrawal]
        self.mock_query.count.return_value = 1
        self.mock_db.query.return_value = self.mock_query

    @patch('app.business.payment.payment_withdrawal.logger')
    async def test_create_withdrawal_success_with_card(self, mock_logger):
        """Test successful withdrawal creation with card."""
        # Arrange
        withdrawal_request = WithdrawalCreate(
            amount_cents=10000,  # $100.00
            withdrawal_type=WType.PAYOUT,
            method=WMethod.CARD,
            currency_code="USD",
            card_id=1,
            description="Test withdrawal"
        )

        # Mock database queries
        currency_query = Mock()
        currency_query.filter.return_value.first.return_value = self.mock_currency
        self.mock_db.query.return_value = currency_query

        # Act
        result = await WithdrawalService.create_withdrawal(
            self.mock_db, self.user, withdrawal_request
        )

        # Assert
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()
        self.mock_db.refresh.assert_called()

        # Check user balance was reduced
        self.assertEqual(self.user.balance, 900.0)  # 1000 - 100

        mock_logger.info.assert_called()

    @patch('app.business.payment.payment_withdrawal.logger')
    async def test_create_withdrawal_success_without_card(self, mock_logger):
        """Test successful withdrawal creation without card."""
        # Arrange
        withdrawal_request = WithdrawalCreate(
            amount_cents=5000,  # $50.00
            withdrawal_type=WType.BANK_TRANSFER,
            method=WMethod.BANK_ACCOUNT,
            currency_code="USD",
            description="Bank transfer test"
        )

        # Mock database queries
        currency_query = Mock()
        currency_query.filter.return_value.first.return_value = self.mock_currency
        self.mock_db.query.return_value = currency_query

        # Act
        result = await WithdrawalService.create_withdrawal(
            self.mock_db, self.user, withdrawal_request
        )

        # Assert
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()
        self.assertEqual(self.user.balance, 950.0)  # 1000 - 50

    @patch('app.business.payment.payment_withdrawal.logger')
    async def test_create_withdrawal_creates_new_currency(self, mock_logger):
        """Test withdrawal creation creates new currency if not exists."""
        # Arrange
        withdrawal_request = WithdrawalCreate(
            amount_cents=10000,
            withdrawal_type=WType.PAYOUT,
            method=WMethod.CARD,
            currency_code="EUR",
            card_id=1
        )

        # Mock database queries - currency not found
        currency_query = Mock()
        currency_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = currency_query

        # Act
        result = await WithdrawalService.create_withdrawal(
            self.mock_db, self.user, withdrawal_request
        )

        # Assert
        # Should create new currency
        self.assertEqual(self.mock_db.add.call_count, 2)  # Currency + Withdrawal
        self.assertEqual(self.mock_db.commit.call_count, 2)  # Currency + final commit

    async def test_create_withdrawal_insufficient_balance(self):
        """Test withdrawal creation fails with insufficient balance."""
        # Arrange
        self.user.balance = 50.0  # Less than withdrawal amount
        withdrawal_request = WithdrawalCreate(
            amount_cents=10000,  # $100.00
            withdrawal_type=WType.PAYOUT,
            method=WMethod.CARD,
            currency_code="USD",
            card_id=1
        )

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await WithdrawalService.create_withdrawal(
                self.mock_db, self.user, withdrawal_request
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Insufficient balance", context.exception.detail)

    async def test_create_withdrawal_card_not_found(self):
        """Test withdrawal creation fails when card not found."""
        # Arrange
        self.user.cards = []  # No cards
        withdrawal_request = WithdrawalCreate(
            amount_cents=10000,
            withdrawal_type=WType.PAYOUT,
            method=WMethod.CARD,
            currency_code="USD",
            card_id=1
        )

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await WithdrawalService.create_withdrawal(
                self.mock_db, self.user, withdrawal_request
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("Card not found", context.exception.detail)

    async def test_create_withdrawal_expired_card(self):
        """Test withdrawal creation fails with expired card."""
        # Arrange
        self.mock_card.is_expired = True
        withdrawal_request = WithdrawalCreate(
            amount_cents=10000,
            withdrawal_type=WType.PAYOUT,
            method=WMethod.CARD,
            currency_code="USD",
            card_id=1
        )

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await WithdrawalService.create_withdrawal(
                self.mock_db, self.user, withdrawal_request
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("Cannot withdraw to expired card", context.exception.detail)

    @patch('app.business.payment.payment_withdrawal.logger')
    async def test_create_withdrawal_general_exception(self, mock_logger):
        """Test withdrawal creation handles general exceptions."""
        # Arrange
        withdrawal_request = WithdrawalCreate(
            amount_cents=10000,
            withdrawal_type=WType.PAYOUT,
            method=WMethod.CARD,
            currency_code="USD",
            card_id=1
        )

        # Mock database to raise exception
        self.mock_db.query.side_effect = Exception("Database error")

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await WithdrawalService.create_withdrawal(
                self.mock_db, self.user, withdrawal_request
            )

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Failed to process withdrawal", context.exception.detail)
        mock_logger.error.assert_called()

    def test_get_user_withdrawals_no_filter(self):
        """Test get_user_withdrawals without filter."""
        # Arrange
        mock_withdrawals = [
            self._create_mock_withdrawal(withdrawal_id=1),
            self._create_mock_withdrawal(withdrawal_id=2)
        ]

        # Set up query mock that returns iterable list
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_withdrawals  # Return iterable list
        self.mock_db.query.return_value = mock_query

        # Act
        result = WithdrawalService.get_user_withdrawals(self.mock_db, self.user, limit=10)

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn("withdrawals", result)
        self.assertEqual(len(result["withdrawals"]), 2)

    def test_get_user_withdrawals_with_status_filter(self):
        """Test get_user_withdrawals with status filter."""
        # Arrange
        mock_withdrawal = self._create_mock_withdrawal(withdrawal_id=1, status=WStatus.PENDING)

        # Set up query mock that returns iterable list
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_withdrawal]  # Return iterable list
        self.mock_db.query.return_value = mock_query

        # Act
        result = WithdrawalService.get_user_withdrawals(
            self.mock_db, self.user, limit=10, status_filter=WStatus.PENDING
        )

        # Assert
        self.assertIsInstance(result, dict)
        self.assertIn("withdrawals", result)
        self.assertEqual(len(result["withdrawals"]), 1)

    def test_get_withdrawal_by_id_success(self):
        """Test successful withdrawal retrieval by ID."""
        # Act
        result = WithdrawalService.get_withdrawal_by_id(self.mock_db, self.user, 1)

        # Assert
        self.assertIsNotNone(result)
        self.mock_db.query.assert_called()

    def test_get_withdrawal_by_id_not_found(self):
        """Test withdrawal retrieval fails when withdrawal not found."""
        # Arrange
        self.user.withdrawals = []  # No withdrawals

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            WithdrawalService.get_withdrawal_by_id(self.mock_db, self.user, 999)

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("Withdrawal not found", context.exception.detail)

    def test_update_withdrawal_status_success(self):
        """Test successful withdrawal status update."""
        # Arrange
        update_data = WithdrawalUpdate(
            status=WStatus.COMPLETED,
            stripe_payout_id="po_updated123"
        )

        # Act
        result = WithdrawalService.update_withdrawal_status(
            self.mock_db, self.user, 1, update_data
        )

        # Assert
        self.assertIsNotNone(result)
        self.mock_db.commit.assert_called_once()

    def test_update_withdrawal_status_completed(self):
        """Test withdrawal status update to completed."""
        # Arrange
        update_data = WithdrawalUpdate(
            status=WStatus.COMPLETED,
            completed_at=datetime.now()
        )

        # Act
        result = WithdrawalService.update_withdrawal_status(
            self.mock_db, self.user, 1, update_data
        )

        # Assert
        self.assertIsNotNone(result)
        self.mock_db.commit.assert_called_once()

    def test_update_withdrawal_status_failed(self):
        """Test withdrawal status update to failed."""
        # Arrange
        update_data = WithdrawalUpdate(
            status=WStatus.FAILED,
            failure_reason="Insufficient funds",
            failed_at=datetime.now()
        )

        # Act
        result = WithdrawalService.update_withdrawal_status(
            self.mock_db, self.user, 1, update_data
        )

        # Assert
        self.assertIsNotNone(result)
        self.mock_db.commit.assert_called_once()

    def test_get_withdrawal_stats_success(self):
        """Test successful retrieval of withdrawal statistics."""
        # Arrange
        completed_withdrawal = Mock()
        completed_withdrawal.amount = 50.0
        completed_withdrawal.is_completed = True

        self.user.withdrawals = [self.mock_withdrawal, completed_withdrawal]
        self.user.completed_withdrawals = [completed_withdrawal]
        self.user.pending_withdrawals = [self.mock_withdrawal]
        self.user.failed_withdrawals = []
        self.user.refunds = []
        self.user.payouts = [self.mock_withdrawal, completed_withdrawal]
        self.user.total_withdrawal_amount = 150.0

        # Act
        result = WithdrawalService.get_withdrawal_stats(self.mock_db, self.user)

        # Assert
        self.assertIsInstance(result, WithdrawalStatsResponse)
        self.assertEqual(result.total_withdrawals, 2)
        self.assertEqual(result.total_amount, 150.0)
        self.assertEqual(result.completed_withdrawals, 1)
        self.assertEqual(result.pending_withdrawals, 1)
        self.assertEqual(result.failed_withdrawals, 0)
        self.assertEqual(result.average_amount, 50.0)  # 50.0 / 1 completed
        self.assertEqual(result.total_refunds, 0)
        self.assertEqual(result.total_payouts, 2)

    def test_get_withdrawal_stats_no_completed_withdrawals(self):
        """Test withdrawal stats when no completed withdrawals exist."""
        # Arrange
        self.user.completed_withdrawals = []
        self.user.total_withdrawal_amount = 0.0

        # Act
        result = WithdrawalService.get_withdrawal_stats(self.mock_db, self.user)

        # Assert
        self.assertEqual(result.average_amount, 0)  # Should not divide by zero

    def test_cancel_withdrawal_not_found(self):
        """Test withdrawal cancellation fails when withdrawal not found."""
        # Arrange
        self.user.withdrawals = []  # No withdrawals

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            WithdrawalService.cancel_withdrawal(self.mock_db, self.user, 999)

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("Withdrawal not found", context.exception.detail)

    def test_cancel_withdrawal_not_pending(self):
        """Test withdrawal cancellation fails when withdrawal is not pending."""
        # Arrange
        completed_withdrawal = self._create_mock_withdrawal(status=WStatus.COMPLETED)
        completed_withdrawal.can_be_cancelled = False
        self.user.withdrawals = [completed_withdrawal]

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            WithdrawalService.cancel_withdrawal(self.mock_db, self.user, 1)

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("Withdrawal not found", context.exception.detail)

    def test_cancel_withdrawal_cannot_be_cancelled(self):
        """Test withdrawal cancellation fails when withdrawal cannot be cancelled."""
        # Arrange
        processing_withdrawal = self._create_mock_withdrawal(status=WStatus.PROCESSING)
        processing_withdrawal.can_be_cancelled = False
        self.user.withdrawals = [processing_withdrawal]

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            WithdrawalService.cancel_withdrawal(self.mock_db, self.user, 1)

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("Withdrawal not found", context.exception.detail)


if __name__ == '__main__':
    unittest.main()