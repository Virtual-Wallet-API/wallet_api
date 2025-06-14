from app.infrestructure.database import SessionLocal
from app.models.user import User
from app.models.card import Card, CardType
from app.models.category import Category
from app.models.contact import Contact
from app.models.deposit import Deposit, DepositStatus, DepositMethod, DepositType
from app.models.withdrawal import Withdrawal, WithdrawalStatus, WithdrawalType, WithdrawalMethod
from app.models.transaction import Transaction, TransactionStatus
from datetime import datetime

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # Users
        user1 = User(username="alice", email="alice@example.com", phone_number="1234567890", hashed_password="password1")
        user2 = User(username="bob", email="bob@example.com", phone_number="0987654321", hashed_password="password2")
        db.add_all([user1, user2])
        db.commit()
        db.refresh(user1)
        db.refresh(user2)

        # Cards (required fields: user_id, last_four, brand, exp_month, exp_year, cardholder_name, stripe_payment_method_id, type)
        card1 = Card(user_id=user1.id, last_four="1234", brand="visa", exp_month=12, exp_year=2030, cardholder_name="Alice", stripe_payment_method_id="pm_alice1", type=CardType.DEBIT)
        card2 = Card(user_id=user2.id, last_four="5678", brand="mastercard", exp_month=11, exp_year=2029, cardholder_name="Bob", stripe_payment_method_id="pm_bob1", type=CardType.CREDIT)
        db.add_all([card1, card2])
        db.commit()
        db.refresh(card1)
        db.refresh(card2)

        # Categories
        cat1 = Category(user_id=user1.id, name="Groceries")
        cat2 = Category(user_id=user2.id, name="Utilities")
        db.add_all([cat1, cat2])
        db.commit()

        # Contacts (only user_id and contact_id)
        contact1 = Contact(user_id=user1.id, contact_id=user2.id)
        contact2 = Contact(user_id=user2.id, contact_id=user1.id)
        db.add_all([contact1, contact2])
        db.commit()

        # Deposits (required: user_id, card_id, payment_method_last_four, currency_id, amount, amount_cents, method, deposit_type, status)
        dep1 = Deposit(user_id=user1.id, card_id=card1.id, payment_method_last_four="1234", currency_id=1, amount=100.0, amount_cents=10000, method=DepositMethod.STRIPE, deposit_type=DepositType.CARD_PAYMENT, status=DepositStatus.COMPLETED, created_at=datetime.now())
        dep2 = Deposit(user_id=user2.id, card_id=card2.id, payment_method_last_four="5678", currency_id=1, amount=200.0, amount_cents=20000, method=DepositMethod.STRIPE, deposit_type=DepositType.CARD_PAYMENT, status=DepositStatus.COMPLETED, created_at=datetime.now())
        db.add_all([dep1, dep2])
        db.commit()

        # Withdrawals (required: user_id, card_id, currency_id, amount, amount_cents, withdrawal_type, method, status)
        wd1 = Withdrawal(user_id=user1.id, card_id=card1.id, currency_id=1, amount=50.0, amount_cents=5000, withdrawal_type=WithdrawalType.PAYOUT, method=WithdrawalMethod.CARD, status=WithdrawalStatus.COMPLETED, created_at=datetime.now())
        wd2 = Withdrawal(user_id=user2.id, card_id=card2.id, currency_id=1, amount=75.0, amount_cents=7500, withdrawal_type=WithdrawalType.PAYOUT, method=WithdrawalMethod.CARD, status=WithdrawalStatus.COMPLETED, created_at=datetime.now())
        db.add_all([wd1, wd2])
        db.commit()

        # Transactions (required: sender_id, receiver_id, amount, status, date, currency_id)
        tx1 = Transaction(sender_id=user1.id, receiver_id=user2.id, amount=20.0, status=TransactionStatus.COMPLETED, date=datetime.now(), currency_id=1)
        tx2 = Transaction(sender_id=user2.id, receiver_id=user1.id, amount=30.0, status=TransactionStatus.COMPLETED, date=datetime.now(), currency_id=1)
        db.add_all([tx1, tx2])
        db.commit()

        print("Sample data inserted successfully.")
    finally:
        db.close() 