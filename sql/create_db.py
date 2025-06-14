from app.infrestructure.database import Base, engine
import app.models.user
import app.models.card
import app.models.category
import app.models.contact
import app.models.currency
import app.models.deposit
import app.models.recurring_transaction_history
import app.models.recurring_transation
import app.models.transaction
import app.models.withdrawal

if __name__ == "__main__":
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database schema created successfully.") 