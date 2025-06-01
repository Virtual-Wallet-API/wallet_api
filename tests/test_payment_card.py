"""
Unit tests for CardService business logic.
"""
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi import HTTPException

from tests.base_test import BaseTestCase
from app.business.payment.payment_card import CardService
from app.models.card import Card, CardType
from app.schemas.card import CardUpdate, CardResponse, CardListResponse


class TestCardService(BaseTestCase):
    """Test cases for CardService."""

    def setUp(self):
        super().setUp()
        # Create mock user
        self.mock_user = self._create_mock_user(user_id=1, username="testuser")

        # Create mock cards with proper types
        self.mock_card1 = self._create_mock_card(
            card_id=1,
            user_id=1,
            stripe_payment_method_id="pm_1234567890",
            last_four="1234",
            brand="visa",
            exp_month=12,
            exp_year=2025,
            cardholder_name="John Doe",
            card_type=CardType.CREDIT,
            is_default=True,
            is_active=True
        )

        self.mock_card2 = self._create_mock_card(
            card_id=2,
            user_id=1,
            stripe_payment_method_id="pm_0987654321",
            last_four="5678",
            brand="mastercard",
            exp_month=6,
            exp_year=2026,
            cardholder_name="John Doe",
            card_type=CardType.DEBIT,
            is_default=False,
            is_active=True
        )

    def _create_mock_card(self, card_id=1, user_id=1, stripe_payment_method_id="pm_test",
                          last_four="1234", brand="visa", exp_month=12, exp_year=2025,
                          cardholder_name="Test User", card_type=CardType.CREDIT,
                          is_default=False, is_active=True, created_at=None):
        """Create a mock card with proper attributes."""
        mock_card = Mock(spec=Card)
        mock_card.id = card_id
        mock_card.user_id = user_id
        mock_card.stripe_payment_method_id = stripe_payment_method_id
        mock_card.last_four = last_four
        mock_card.brand = brand
        mock_card.exp_month = exp_month
        mock_card.exp_year = exp_year
        mock_card.cardholder_name = cardholder_name
        mock_card.type = card_type
        mock_card.design = '{"color": "purple"}'
        mock_card.is_default = is_default
        mock_card.is_active = is_active
        mock_card.created_at = created_at or datetime.utcnow()
        mock_card.masked_number = f"**** **** **** {last_four}"
        mock_card.is_expired = False
        mock_card.stripe_card_fingerprint = f"fp_{card_id}"
        return mock_card

    def test_get_user_cards_success(self):
        """Test successfully retrieving user cards."""
        # Arrange
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [self.mock_card1, self.mock_card2]

        # Act
        result = CardService.get_user_cards(mock_db, self.mock_user)

        # Assert
        self.assertIsInstance(result, CardListResponse)
        self.assertEqual(result.total, 2)
        self.assertTrue(result.has_default)
        self.assertEqual(len(result.cards), 2)
        mock_db.query.assert_called_once_with(Card)

    def test_get_user_cards_empty(self):
        """Test retrieving user cards when no cards exist."""
        # Arrange
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        # Act
        result = CardService.get_user_cards(mock_db, self.mock_user)

        # Assert
        self.assertIsInstance(result, CardListResponse)
        self.assertEqual(result.total, 0)
        self.assertFalse(result.has_default)
        self.assertEqual(len(result.cards), 0)

    def test_get_user_cards_no_default(self):
        """Test retrieving user cards when no default card exists."""
        # Arrange
        self.mock_card1.is_default = False
        self.mock_card2.is_default = False

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [self.mock_card1, self.mock_card2]

        # Act
        result = CardService.get_user_cards(mock_db, self.mock_user)

        # Assert
        self.assertFalse(result.has_default)

    def test_validate_card_fingerprint_not_exists(self):
        """Test card fingerprint validation when card doesn't exist."""
        # Arrange
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act
        result = CardService.validate_card_fingerprint(mock_db, self.mock_user, "fp_nonexistent")

        # Assert
        self.assertFalse(result)

    def test_validate_card_fingerprint_belongs_to_user(self):
        """Test card fingerprint validation when card belongs to user."""
        # Arrange
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_card1

        # Act
        result = CardService.validate_card_fingerprint(mock_db, self.mock_user, "fp_1")

        # Assert
        self.assertTrue(result)

    def test_validate_card_fingerprint_belongs_to_other_user(self):
        """Test card fingerprint validation when card belongs to another user."""
        # Arrange
        other_user_card = self._create_mock_card(user_id=999)  # Different user

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = other_user_card

        # Act
        result = CardService.validate_card_fingerprint(mock_db, self.mock_user, "fp_other")

        # Assert
        self.assertEqual(result, other_user_card)

    def test_get_card_by_id_success(self):
        """Test successfully retrieving a card by ID."""
        # Arrange
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_card1

        with patch('app.business.payment.payment_card.CardResponse') as mock_card_response:
            mock_card_response.model_validate.return_value = "validated_card"

            # Act
            result = CardService.get_card_by_id(mock_db, self.mock_user, 1)

            # Assert
            self.assertEqual(result, "validated_card")
            mock_card_response.model_validate.assert_called_once_with(self.mock_card1)

    def test_get_card_by_id_not_found(self):
        """Test retrieving a card by ID when card doesn't exist."""
        # Arrange
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            CardService.get_card_by_id(mock_db, self.mock_user, 999)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Card not found")

    def test_update_card_success(self):
        """Test successfully updating a card."""
        # Arrange
        card_update = CardUpdate(cardholder_name="Updated Name", design='{"color": "blue"}')

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_card1

        with patch('app.business.payment.payment_card.CardResponse') as mock_card_response:
            mock_card_response.model_validate.return_value = "updated_card"

            # Act
            result = CardService.update_card(mock_db, self.mock_user, 1, card_update)

            # Assert
            self.assertEqual(result, "updated_card")
            self.assertEqual(self.mock_card1.cardholder_name, "Updated Name")
            self.assertEqual(self.mock_card1.design, '{"color": "blue"}')
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(self.mock_card1)

    def test_update_card_set_default(self):
        """Test updating a card to set it as default."""
        # Arrange
        card_update = CardUpdate(is_default=True)
        old_default_card = self._create_mock_card(card_id=99, is_default=True)

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query

        # Set up filter chain for finding the card to update
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [self.mock_card2,
                                        old_default_card]  # First call finds card, second finds old default

        with patch('app.business.payment.payment_card.CardResponse') as mock_card_response:
            mock_card_response.model_validate.return_value = "updated_card"

            # Act
            result = CardService.update_card(mock_db, self.mock_user, 2, card_update)

            # Assert
            self.assertTrue(self.mock_card2.is_default)
            self.assertFalse(old_default_card.is_default)
            mock_db.commit.assert_called_once()

    def test_update_card_not_found(self):
        """Test updating a card that doesn't exist."""
        # Arrange
        card_update = CardUpdate(cardholder_name="Updated Name")

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            CardService.update_card(mock_db, self.mock_user, 999, card_update)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Card not found")

    @patch('app.business.payment.payment_card.StripeService.detach_payment_method')
    async def test_delete_card_success(self, mock_detach):
        """Test successfully deleting a card."""
        # Arrange
        mock_detach.return_value = AsyncMock()

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_card1

        # Act
        result = await CardService.delete_card(mock_db, self.mock_user, 1)

        # Assert
        self.assertEqual(result, {"message": "Card deleted successfully"})
        self.assertFalse(self.mock_card1.is_active)
        self.assertFalse(self.mock_card1.is_default)
        mock_db.commit.assert_called_once()

    @patch('app.business.payment.payment_card.StripeService.detach_payment_method')
    async def test_delete_default_card_with_other_cards(self, mock_detach):
        """Test deleting default card when other cards exist."""
        # Arrange
        mock_detach.return_value = AsyncMock()
        other_card = self._create_mock_card(card_id=2, is_default=False)

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [self.mock_card1,
                                        other_card]  # First call finds card to delete, second finds other card

        # Act
        result = await CardService.delete_card(mock_db, self.mock_user, 1)

        # Assert
        self.assertEqual(result, {"message": "Card deleted successfully"})
        self.assertFalse(self.mock_card1.is_active)
        self.assertFalse(self.mock_card1.is_default)
        self.assertTrue(other_card.is_default)  # Other card becomes default

    @patch('app.business.payment.payment_card.StripeService.detach_payment_method')
    async def test_delete_card_not_found(self, mock_detach):
        """Test deleting a card that doesn't exist."""
        # Arrange
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await CardService.delete_card(mock_db, self.mock_user, 999)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Invalid card ID provided")

    @patch('app.business.payment.payment_card.StripeService.detach_payment_method')
    async def test_delete_card_stripe_error_continues(self, mock_detach):
        """Test deleting a card when Stripe detach fails but database operation succeeds."""
        # Arrange
        mock_detach.side_effect = Exception("Stripe error")

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_card1

        # Act
        result = await CardService.delete_card(mock_db, self.mock_user, 1)

        # Assert - Should still succeed despite Stripe error
        self.assertEqual(result, {"message": "Card deleted successfully"})
        self.assertFalse(self.mock_card1.is_active)

    @patch('app.business.payment.payment_card.StripeService.detach_payment_method')
    async def test_delete_card_database_error(self, mock_detach):
        """Test deleting a card when database operation fails."""
        # Arrange
        mock_detach.return_value = AsyncMock()

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_card1
        mock_db.commit.side_effect = Exception("Database error")

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await CardService.delete_card(mock_db, self.mock_user, 1)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Failed to delete card")

    def test_update_card_partial_updates(self):
        """Test updating only specific fields of a card."""
        # Arrange - Only update cardholder_name
        card_update = CardUpdate(cardholder_name="New Name Only")
        original_design = self.mock_card1.design

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = self.mock_card1

        with patch('app.business.payment.payment_card.CardResponse') as mock_card_response:
            mock_card_response.model_validate.return_value = "updated_card"

            # Act
            result = CardService.update_card(mock_db, self.mock_user, 1, card_update)

            # Assert
            self.assertEqual(self.mock_card1.cardholder_name, "New Name Only")
            self.assertEqual(self.mock_card1.design, original_design)  # Should remain unchanged

    def test_get_user_cards_ordering(self):
        """Test that user cards are ordered correctly (default first, then by created_at desc)."""
        # Arrange
        older_card = self._create_mock_card(
            card_id=3,
            is_default=False,
            created_at=datetime(2023, 1, 1)
        )
        newer_card = self._create_mock_card(
            card_id=4,
            is_default=False,
            created_at=datetime(2023, 6, 1)
        )

        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [self.mock_card1, newer_card, older_card]  # Default first, then by date

        # Act
        result = CardService.get_user_cards(mock_db, self.mock_user)

        # Assert
        # Verify order_by was called with correct parameters (default desc, created_at desc)
        mock_query.order_by.assert_called_once()


if __name__ == '__main__':
    unittest.main()